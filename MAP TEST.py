import sys
import pygame
import csv

TILE_SIZE = 40  # Size of each grid square in pixels
COLOR_MAP = {
    '0': (220, 220, 220),  # Light Gray (Floor)
    '1': (80, 80, 80),      # Dark Gray (Wall)
    '2': (100, 150, 220),   # Blue Tile
    '3': (40, 40, 40),      # Black Tile
    '4': (240, 180, 130),   # Orange Tile
    '5': (180, 210, 180)    # Green Tile
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

        # Load CSV Map
        self.tile_map = []
        self.load_map("MAP - Level 3 (1).csv")

        # Set initial player and enemy positions on a valid floor tile (row 0, col 7)
        self.player_x = 7 * TILE_SIZE + 20
        self.player_y = 0 * TILE_SIZE + 20

        self.enemy_size = 20
        self.enemy_speed = 4
        self.enemy_x = 8 * TILE_SIZE + 20
        self.enemy_y = 0 * TILE_SIZE + 20

        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.run_game()

    def load_map(self, filename):
        """Loads CSV map data; stores NaN or empty strings as None."""
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    map_row = []
                    for col in row:
                        val = col.strip()
                        if val and val.lower() != 'nan':
                            val = str(int(float(val)))
                        else:
                            val = None  # Non-valued space
                        map_row.append(val)
                    self.tile_map.append(map_row)
        except FileNotFoundError:
            print(f"Error: {filename} not found.")

    def get_camera_pos(self, screen_w, screen_h):
        """
        Calculates camera coordinates clamped strictly within the bounds of 
        valid (non-None) tiles around the player to prevent showing empty space.
        """
        p_row = max(0, min(int(self.player_y // TILE_SIZE), len(self.tile_map) - 1))
        p_col = max(0, min(int(self.player_x // TILE_SIZE), len(self.tile_map[0]) - 1))

        # Scan left and right along the current player row for valid tile boundaries
        left_c = p_col
        while left_c > 0 and self.tile_map[p_row][left_c - 1] is not None:
            left_c -= 1
        right_c = p_col
        while right_c < len(self.tile_map[0]) - 1 and self.tile_map[p_row][right_c + 1] is not None:
            right_c += 1

        # Scan up and down along the current player column for valid tile boundaries
        top_r = p_row
        while top_r > 0 and self.tile_map[top_r - 1][p_col] is not None:
            top_r -= 1
        bottom_r = p_row
        while bottom_r < len(self.tile_map) - 1 and self.tile_map[bottom_r + 1][p_col] is not None:
            bottom_r += 1

        # Pixel bounds of valid tiles surrounding player
        min_x = left_c * TILE_SIZE
        max_x = (right_c + 1) * TILE_SIZE
        min_y = top_r * TILE_SIZE
        max_y = (bottom_r + 1) * TILE_SIZE

        # Clamp Camera X
        if max_x - min_x <= screen_w:
            cam_x = min_x - (screen_w - (max_x - min_x)) / 2
        else:
            cam_x = max(min_x, min(self.player_x - screen_w / 2, max_x - screen_w))

        # Clamp Camera Y
        if max_y - min_y <= screen_h:
            cam_y = min_y - (screen_h - (max_y - min_y)) / 2
        else:
            cam_y = max(min_y, min(self.player_y - screen_h / 2, max_y - screen_h))

        return cam_x, cam_y

    def check_collision(self, next_x, next_y, object_size):
        half = object_size / 2
        p_left = next_x - half
        p_right = next_x + half
        p_top = next_y - half
        p_bottom = next_y + half

        min_col = int(p_left // TILE_SIZE)
        max_col = int(p_right // TILE_SIZE)
        min_row = int(p_top // TILE_SIZE)
        max_row = int(p_bottom // TILE_SIZE)

        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                if r < 0 or r >= len(self.tile_map) or c < 0 or c >= len(self.tile_map[0]):
                    return True
                
                val = self.tile_map[r][c]
                if val is None or val in SOLID_TILES:
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

            if not self.check_collision(next_ex, self.enemy_y, self.enemy_size):
                self.enemy_x = next_ex
            if not self.check_collision(self.enemy_x, next_ey, self.enemy_size):
                self.enemy_y = next_ey

    def check_enemy_hit(self):
        half_p = self.player_size / 2
        half_e = self.enemy_size / 2

        return not (
            self.player_x + half_p <= self.enemy_x - half_e
            or self.player_x - half_p >= self.enemy_x + half_e
            or self.player_y + half_p <= self.enemy_y - half_e
            or self.player_y - half_p >= self.enemy_y + half_e
        )

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

            if dx != 0 and not self.check_collision(self.player_x + dx, self.player_y, self.player_size):
                self.player_x += dx
            if dy != 0 and not self.check_collision(self.player_x, self.player_y + dy, self.player_size):
                self.player_y += dy

            self.update_enemy()

            self.screen.fill((15, 15, 20))
            screen_w, screen_h = self.screen.get_size()

            # Dynamic Camera Clamping: Keeps empty NaN tiles off screen
            cam_x, cam_y = self.get_camera_pos(screen_w, screen_h)

            for r_idx, row in enumerate(self.tile_map):
                for c_idx, tile_id in enumerate(row):
                    if tile_id is not None and tile_id in COLOR_MAP:
                        world_x = c_idx * TILE_SIZE
                        world_y = r_idx * TILE_SIZE

                        screen_x = world_x - cam_x
                        screen_y = world_y - cam_y

                        if -TILE_SIZE <= screen_x <= screen_w and -TILE_SIZE <= screen_y <= screen_h:
                            tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                            pygame.draw.rect(self.screen, COLOR_MAP[tile_id], tile_rect)

            player_screen_x = self.player_x - cam_x
            player_screen_y = self.player_y - cam_y
            half_p = self.player_size / 2
            player_rect = pygame.Rect(
                player_screen_x - half_p,
                player_screen_y - half_p,
                self.player_size,
                self.player_size,
            )
            pygame.draw.rect(self.screen, (146, 238, 255), player_rect)

            enemy_screen_x = self.enemy_x - cam_x
            enemy_screen_y = self.enemy_y - cam_y
            half_e = self.enemy_size / 2
            enemy_rect = pygame.Rect(
                enemy_screen_x - half_e,
                enemy_screen_y - half_e,
                self.enemy_size,
                self.enemy_size,
            )
            pygame.draw.rect(self.screen, (225, 40, 40), enemy_rect)

            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(center=(player_screen_x, player_screen_y - 30))
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    App()
