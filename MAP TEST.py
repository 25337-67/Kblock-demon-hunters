import pygame
import sys

# 1. Initialize Pygame
pygame.init()

TILE_SIZE = 32
GRID_WIDTH = 20
GRID_HEIGHT = 15
SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE   
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE 

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Tilemap with Player")
clock = pygame.time.Clock()

# Map Layout ('W' = Wall, 'G' = Grass, 'D' = Dirt)
GAME_MAP = [
    ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W"],
    ["W", "G", "G", "G", "G", "W", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "W", "G", "D", "D", "D", "D", "G", "G", "G", "G", "G", "G", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "W", "G", "D", "G", "G", "D", "G", "W", "W", "W", "W", "W", "G", "G", "W"],
    ["W", "G", "G", "G", "G", "G", "G", "D", "G", "G", "D", "G", "W", "G", "G", "G", "W", "G", "G", "W"],
    ["W", "W", "W", "W", "G", "W", "W", "D", "G", "G", "D", "G", "W", "G", "D", "G", "W", "G", "G", "W"],
    ["W", "G", "G", "G", "G", "W", "G", "G", "G", "G", "D", "G", "G", "G", "D", "G", "W", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "W", "G", "W", "W", "W", "W", "W", "W", "W", "D", "G", "W", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "G", "G", "W", "G", "G", "G", "G", "G", "W", "G", "G", "W", "G", "G", "W"],
    ["W", "G", "G", "G", "G", "W", "G", "W", "G", "G", "G", "G", "G", "W", "G", "G", "W", "G", "G", "W"],
    ["W", "W", "W", "G", "W", "W", "G", "W", "W", "W", "G", "W", "W", "W", "W", "G", "W", "G", "G", "W"],
    ["W", "G", "G", "G", "G", "W", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "W", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "G", "G", "W"],
    ["W", "G", "D", "D", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "G", "W"],
    ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W", "W"]
]

# Assets dictionary
assets = {
    "W": pygame.Surface((TILE_SIZE, TILE_SIZE)),
    "G": pygame.Surface((TILE_SIZE, TILE_SIZE)),
    "D": pygame.Surface((TILE_SIZE, TILE_SIZE))
}
assets["W"].fill((100, 100, 100)) 
assets["G"].fill((34, 139, 34))   
assets["D"].fill((139, 69, 19))   

# 2. Define the Player Class
class Player:
    def __init__(self, x, y):
        # Position using Pygame Vectors for precise movement math
        self.pos = pygame.math.Vector2(x, y)
        self.speed = 4
        self.size = 24  # Slightly smaller than a tile (32) to move through gaps easily
        
        # Create a simple blue circle surface for the player graphic
        self.surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.surface, (0, 100, 255), (self.size // 2, self.size // 2), self.size // 2)

    def check_collision(self, new_pos, game_map):
        """Creates a target rectangle and checks if it overlaps with any Wall ('W') tile."""
        target_rect = pygame.Rect(new_pos.x, new_pos.y, self.size, self.size)
        
        for row_idx, row in enumerate(game_map):
            for col_idx, tile_type in enumerate(row):
                if tile_type == "W":
                    # Generate a collision box for this wall tile
                    wall_rect = pygame.Rect(col_idx * TILE_SIZE, row_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if target_rect.colliderect(wall_rect):
                        return True # Collision detected
        return False # Safe to move

    def handle_input(self, game_map):
        """Reads keyboard state and processes movement dynamically."""
        keys = pygame.key.get_pressed()
        move_dir = pygame.math.Vector2(0, 0)

        # Gather directional intent
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_dir.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_dir.y = 1

        # Normalize diagonal movement speed so you don't run faster sideways
        if move_dir.length() > 0:
            move_dir = move_dir.normalize() * self.speed

        # Axis-separated movement handles sliding along walls smoothly
        if move_dir.x != 0:
            target_pos = pygame.math.Vector2(self.pos.x + move_dir.x, self.pos.y)
            if not self.check_collision(target_pos, game_map):
                self.pos.x = target_pos.x

        if move_dir.y != 0:
            target_pos = pygame.math.Vector2(self.pos.x, self.pos.y + move_dir.y)
            if not self.check_collision(target_pos, game_map):
                self.pos.y = target_pos.y

    def draw(self, surface):
        surface.blit(self.surface, self.pos)

def draw_map(surface, game_map, tile_assets, tile_size):
    for row_idx, row in enumerate(game_map):
        for col_idx, tile_type in enumerate(row):
            if tile_type in tile_assets:
                surface.blit(tile_assets[tile_type], (col_idx * tile_size, row_idx * tile_size))

# 3. Instantiate the Player (placed inside the initial grass pathway)
player = Player(x=40, y=40)

# Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # Process Player Actions
    player.handle_input(GAME_MAP)
    
    # Rendering Updates
    screen.fill((0, 0, 0))
    draw_map(screen, GAME_MAP, assets, TILE_SIZE)
    player.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
