import csv
import sys
import pygame

# Map Configuration
TILE_SIZE = 40  # Size of each grid square in world units/pixels
COLOR_MAP = {
    '0': (220, 220, 220),  # Light Gray (Floor)
    '1': (80, 80, 80),      # Dark Gray (Wall)
    '2': (100, 150, 220),   # Blue Tile
    '3': (0, 0, 0),         # Black Tile
    '4': (240, 180, 130)    # Orange Tile
}
SOLID_TILES = {'1', '3'}    # Tile IDs that act as collidable walls


class App:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Northcote K-block demon hunters")
        self.clock = pygame.time.Clock()

        self.speed = 5
        self.player_size = 20

        # Player health system
        self.max_health = 3
        self.player_health = 3
        self.hit_cooldown = 0
        self.max_hit_cooldown = 60

        # Load CSV Map and setup boundaries
        self.grid = self.load_map("map4s.csv")
        self.map_width = max(len(row) for row in self.grid) * TILE_SIZE
        self.map_height = len(self.grid) * TILE_SIZE
        self.walls_world = self.extract_walls_from_grid()

        # World Position of the player
        self.player_x = TILE_SIZE * 1.5
        self.player_y = TILE_SIZE * 1.5

        # Enemy setup
        self.enemy_size = 20
        self.enemy_speed = 3
        self.enemy_x = TILE_SIZE * 5
        self.enemy_y = TILE_SIZE * 5

        # Font setup
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

        # Heart sprite setup
        self.img_full = pygame.image.load("full_heart.png").convert_alpha()
        self.img_half = pygame.image.load("half_heart.png").convert_alpha()
        self.img_empty = pygame.image.load("empty_heart.png").convert_alpha()

        heart_size = (24, 24)
        self.img_full = pygame.transform.scale(self.img_full, heart_size)
        self.img_half = pygame.transform.scale(self.img_half, heart_size)
        self.img_empty = pygame.transform.scale(self.img_empty, heart_size)

        self.run_game()

    def load_map(self, map4_filename):
        grid = []
        try:
            with open(map4_filename, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        grid.append(row)
        except FileNotFoundError:
            grid = [
                ['1', '1', '1', '1', '1'],
                ['1', '0', '0', '0', '1'],
                ['1', '0', '0', '0', '1'],
                ['1', '1', '1', '1', '1']
            ]
        return grid

    def extract_walls_from_grid(self):
        walls = []
        for r_idx, row in enumerate(self.grid):
            for c_idx, tile_id in enumerate(row):
                if tile_id.strip() in SOLID_TILES:
                    x1 = c_idx * TILE_SIZE
                    y1 = r_idx * TILE_SIZE
                    x2 = x1 + TILE_SIZE
                    y2 = y1 + TILE_SIZE
                    walls.append((x1, y1, x2, y2))
        return walls

    def check_collision(self, next_x, next_y):
        half_size = self.player_size / 2
        
        # Prevent leaving outer map bounds
        if (next_x - half_size < 0 or next_x + half_size > self.map_width or
            next_y - half_size < 0 or next_y + half_size > self.map_height):
            return True

        p_left, p_right = next_x - half_size, next_x + half_size
        p_top, p_bottom = next_y - half_size, next_y + half_size

        for wx1, wy1, wx2, wy2 in self.walls_world:
            if not (p_right <= wx1 or p_left >= wx2 or p_bottom <= wy1 or p_top >= wy2):
                return True
        return False

    def check_enemy_wall_collision(self, next_x, next_y):
        half_e = self.enemy_size / 2
        e_left, e_right = next_x - half_e, next_x + half_e
        e_top, e_bottom = next_y - half_e, next_y + half_e

        for wx1, wy1, wx2, wy2 in self.walls_world:
            if not (e_right <= wx1 or e_left >= wx2 or e_bottom <= wy1 or e_top >= wy2):
                return True
        return False

    def update_enemy(self):
        if self.check_enemy_hit():
            return
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        dist = (dx**2 + dy**2) ** 0.5

        if dist != 0:
            next_ex = self.enemy_x + (dx / dist) * self.enemy_speed
            next_ey = self.enemy_y + (dy / dist) * self.enemy_speed

            if not self.check_enemy_wall_collision(next_ex, self.enemy_y):
                self.enemy_x = next_ex
            if not self.check_enemy_wall_collision(self.enemy_x, next_ey):
                self.enemy_y = next_ey

    def check_enemy_hit(self):
        half_p = self.player_size / 2
        half_e = self.enemy_size / 2

        p_left, p_right = self.player_x - half_p, self.player_x + half_p
        p_top, p_bottom = self.player_y - half_p, self.player_y + half_p

        e_left, e_right = self.enemy_x - half_e, self.enemy_x + half_e
        e_top, e_bottom = self.enemy_y - half_e, self.enemy_y + half_e

        if not (p_right <= e_left or p_left >= e_right or p_bottom <= e_top or p_top >= e_bottom):
            return True
        return False

    def drawing_ofplayer_health(self):
        start_x, start_y, spacing = 25, 25, 35
        for i in range(self.max_health):
            container_hp = self.player_health - i
            if container_hp >= 1.0:
                sprite = self.img_full
            elif container_hp == 0.5:
                sprite = self.img_half
            else:
                sprite = self.img_empty
            self.screen.blit(sprite, (start_x + (i * spacing), start_y))

    def draw_map_tiles(self, cam_x, cam_y, screen_w, screen_h):
        center_x, center_y = screen_w / 2, screen_h / 2
        for r_idx, row in enumerate(self.grid):
            for c_idx, tile_id in enumerate(row):
                color = COLOR_MAP.get(tile_id.strip(), (200, 200, 200))
                world_x = c_idx * TILE_SIZE
                world_y = r_idx * TILE_SIZE

                screen_x = world_x - cam_x + center_x
                screen_y = world_y - cam_y + center_y

                tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, color, tile_rect)

    def run_game(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= self.speed
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += self.speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= self.speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += self.speed

            if dx != 0 and not self.check_collision(self.player_x + dx, self.player_y):
                self.player_x += dx
            if dy != 0 and not self.check_collision(self.player_x, self.player_y + dy):
                self.player_y += dy

            self.update_enemy()

            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1

            if self.check_enemy_hit():
                if self.hit_cooldown == 0 and self.player_health > 0:
                    self.player_health -= 0.5
                    self.hit_cooldown = self.max_hit_cooldown

            screen_w, screen_h = self.screen.get_size()
            center_x, center_y = screen_w / 2, screen_h / 2

            # Clamp camera to stop at the edge of the map
            cam_x = max(center_x, min(self.player_x, self.map_width - center_x))
            cam_y = max(center_y, min(self.player_y, self.map_height - center_y))

            self.screen.fill((0, 0, 0))

            # Render tiles relative to clamped camera
            self.draw_map_tiles(cam_x, cam_y, screen_w, screen_h)

            # Draw Player relative to camera
            px = (self.player_x - cam_x + center_x) - (self.player_size / 2)
            py = (self.player_y - cam_y + center_y) - (self.player_size / 2)
            pygame.draw.rect(self.screen, (146, 238, 255), pygame.Rect(px, py, self.player_size, self.player_size))

            # Draw Enemy relative to camera
            ex = (self.enemy_x - cam_x + center_x) - (self.enemy_size / 2)
            ey = (self.enemy_y - cam_y + center_y) - (self.enemy_size / 2)
            pygame.draw.rect(self.screen, (220, 50, 50), pygame.Rect(ex, ey, self.enemy_size, self.enemy_size))

            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(center=(center_x, center_y - 30))
                self.screen.blit(text_surface, text_rect)

            self.drawing_ofplayer_health()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App()
