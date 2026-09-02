import sys
import pygame


class App:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Northcote K-block demon hunters")
        self.clock = pygame.time.Clock()

        self.speed = 5
        self.player_size = 20

        # World Position of the player
        self.player_x = 0
        self.player_y = 0

        # da enemy setup
        # this is the dimensions of the enemy collision box 20x20 pixels square
        self.enemy_size = 20
        # the movement step per frame in pixels moves 5 units to the player every tick
        self.enemy_speed = 5
        # the initial spawning position in world coordinates which is relative to player origin
        self.enemy_x = 300  # Starts 300 units to the right of origin
        self.enemy_y = 200  # Starts 200 units below origin

        # the font setup for the hit text marker
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

        # Define Wall obstacles in World Coordinates: (x1, y1, x2, y2)
        self.walls_world = [
            (-100, -150, 100, -100),  # Top wall
            (150, -100, 200, 200),  # Right side pillar
            (-200, -150, -150, 150),
        ]

        self.run_game()

    def check_collision(self, next_x, next_y):
        half_size = self.player_size / 2
        p_left = next_x - half_size
        p_right = next_x + half_size
        p_top = next_y - half_size
        p_bottom = next_y + half_size

        for wx1, wy1, wx2, wy2 in self.walls_world:
            # the correct Axis-Aligned Bounding Box collision checks
            # If player is completely to the left, right, top, or bottom of wall, NO collision.
            if not (
                p_right <= wx1
                or p_left >= wx2
                or p_bottom <= wy1
                or p_top >= wy2
            ):
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
        #Enemy only moves if not touching player
        if self.check_enemy_hit():
            return
        # this moves the enemy towards da players main positions
        # the calculation for the distance vector components from enemy to player
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        # distance formula
        dist = (dx**2 + dy**2) ** 0.5

        if dist != 0:
        
            # enemy to move toward the player's position
            self.enemy_x += (dx / dist) * self.enemy_speed
            self.enemy_y += (dy / dist) * self.enemy_speed

            # Only update enemy coordinate if it won't intersect with a wall
        if not self.check_enemy_wall_collision(next_ex, self.enemy_y):
            self.enemy_x = next_ex
        if not self.check_enemy_wall_collision(self.enemy_x, next_ey):
            self.enemy_y = next_ey

    def check_enemy_hit(self):
        #Checks bounding box collision between player and enemy.
        half_p = self.player_size / 2
        half_e = self.enemy_size / 2

        # players axis-aligned Bounding Box boundaries
        p_left, p_right = self.player_x - half_p, self.player_x + half_p
        p_top, p_bottom = self.player_y - half_p, self.player_y + half_p

        # enemy  axis-aligned Bounding Box boundaries
        e_left, e_right = self.enemy_x - half_e, self.enemy_x + half_e
        e_top, e_bottom = self.enemy_y - half_e, self.enemy_y + half_e

        # Overlap test
        if not (
            p_right <= e_left
            or p_left >= e_right
            or p_bottom <= e_top
            or p_top >= e_bottom
        ):
            return True
        return False

    def run_game(self):
        running = True
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

            # Controls
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= self.speed
                print('work')
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += self.speed
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= self.speed
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += self.speed

            # Update Position with Collisions
            if dx != 0 and not self.check_collision(
                self.player_x + dx, self.player_y
            ):
                self.player_x += dx
            if dy != 0 and not self.check_collision(
                self.player_x, self.player_y + dy
            ):
                self.player_y += dy

            # this updates the enemy position
            self.update_enemy()

            # Render Frame
            self.screen.fill((240, 240, 240))  # Background #F0F0F0
            screen_w, screen_h = self.screen.get_size()
            center_x, center_y = screen_w / 2, screen_h / 2

            # Draw Walls relative to camera
            for wx1, wy1, wx2, wy2 in self.walls_world:
                sx1 = wx1 - self.player_x + center_x
                sy1 = wy1 - self.player_y + center_y
                sx2 = wx2 - self.player_x + center_x
                sy2 = wy2 - self.player_y + center_y

                wall_rect = pygame.Rect(sx1, sy1, sx2 - sx1, sy2 - sy1)
                pygame.draw.rect(
                    self.screen, (255, 107, 107), wall_rect
                )  # #FF6B6B

            # Draw Player at screen center
            half_p = self.player_size / 2
            player_rect = pygame.Rect(
                center_x - half_p,
                center_y - half_p,
                self.player_size,
                self.player_size,
            )
            pygame.draw.rect(
                self.screen, (146, 238, 255), player_rect
            )  

            # this positions the enemy relative to the players position in the world
            # turns the enemy world coordinates to relative screen coordinates 
            half_e = self.enemy_size / 2
            ex1 = (self.enemy_x - self.player_x + center_x) - half_e
            ey1 = (self.enemy_y - self.player_y + center_y) - half_e
            enemy_rect = pygame.Rect(
                ex1, ey1, self.enemy_size, self.enemy_size
            )

            # this draws the enemy visual 
            pygame.draw.rect(self.screen, (5, 0, 139), enemy_rect)

            # this displays "HIT!
            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(
                    center=(center_x, center_y - 30)
                )
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()
            self.clock.tick(60)  # Lock to 60 FPS (~16ms per frame)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App()
