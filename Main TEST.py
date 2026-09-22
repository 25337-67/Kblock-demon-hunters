import sys
import pygame
import csv #Google Sheets map

TILE_SIZE = 40  # Size of each grid square in pixels
COLOR_MAP = {   # RGB
    '0': (255, 255, 255),  # White (Wall)
    '1': (80, 80, 80),      # Dark Gray (Wall)
    '2': (100, 150, 220),   # Blue Tile (Window)
    '3': (40, 40, 40),      # Black Tile (Door)
    '4': (240, 180, 130),   # Orange Tile (Wall)
    '5': (140, 140, 140),   # Light Gray (Floor)
    '6': (200, 200, 200)    # Lightish Gray (Outside Floor)
}
SOLID_TILES = {'1', '2', '3', '4'}  # Walls


class App:

    def __init__(self):
        #Boot up Pygame
        pygame.init() #initialise pygame
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) #Open in fullscreen
        pygame.display.set_caption("Northcote K-block demon hunters") #Window title
        self.clock = pygame.time.Clock() #For capping FPS later
        #Player specs
        self.speed = 5
        self.player_size = 20

        #Player health setup 
        self.max_health = 3 #max health caopacity
        # the current health remaining for the player
        self.player_health = 3
        # the cooldown to prevent losing all 3 hearts instantly when coming into contact with the enemy
        self.hit_cooldown = 0
        # Iframe duration 60 frames = 1 second buffer at 60 FPS
        self.max_hit_cooldown = 60 


        # Load CSV map and set spawns
        self.tile_map = []
        self.load_map("MAP - Level 3 (2).csv") #Map file name
        self.set_spawns_from_map()

        # da enemy setup
        # this is the dimensions of the enemy collision box 20x20 pixels square
        self.enemy_size = 20
        # the movement step per frame in pixels moves 5 units to the player every tick
        self.enemy_speed = 5

        # the state tracking for the 3 second stun on the enemy after a correct answer
        self.enemy_stun_timer = 0  # the counter in frames (180 frames = 3 seconds at 60 FPS)

        # the State tracking for question popup 
        self.in_question_mode = False  # the flag to pause movement and display the dialogue overlay
        self.question_timer = 0        # the timer in frames for answering (300 frames = 5 seconds)
        self.typewriter_index = 0      # the character counter for animating the question text letter by letter
        self.dialogue_full_text = "yo g, Are apples red?"  # the full text string for the dialogue box

        # the font setup for the hit text marker
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

        # the fonts are styled for dialogue box 
        self.font = pygame.font.SysFont("Courier New", 22, bold=True)
        self.subfont = pygame.font.SysFont("Courier New", 18, bold=True)


        # this loads the heart sprite images 
        self.img_full = pygame.image.load("full_heart.png").convert_alpha()
        self.img_half = pygame.image.load("half_heart.png").convert_alpha()
        self.img_empty = pygame.image.load("empty_heart.png").convert_alpha()

        heart_size = (24, 24)#scales the heart sprites to 24x24 for the screen
        self.img_full = pygame.transform.scale(self.img_full, heart_size)
        self.img_half = pygame.transform.scale(self.img_half, heart_size)
        self.img_empty = pygame.transform.scale(self.img_empty, heart_size)

        #Start the game loop
        self.run_game()

    def load_map(self, filename):
        #Loads CSV map data; handles numbers and spawn tags ('P', 'E').
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    map_row = []
                    for col in row:
                        val = col.strip() #clean up empty cells
                        if val and val.lower() != 'nan': #nan output from google sheets is treated as empty space
                            try:
                                val = str(int(float(val))) #convert floating numbers to clean integers
                            except ValueError:
                                val = val.upper()  # Keep string markers like 'P' or 'E'
                        else:
                            val = None  # Empty space
                        map_row.append(val)
                    self.tile_map.append(map_row)
        except FileNotFoundError:
            print(f"Error: {filename} not found.")

    def set_spawns_from_map(self):
        #Default fallback spawn coordinates (Column, Row)
        player_col, player_row = 7, 0
        enemy_col, enemy_row = 8, 0

        for r_idx, row in enumerate(self.tile_map):# Scan map for spawn letters 'P' and 'E'
            for c_idx, tile in enumerate(row):
                if tile == 'P': #Player spawn
                    player_col, player_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = '5'  # Replace marker with floor tile
                elif tile == 'E': #Enemy spawn
                    enemy_col, enemy_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = '5'  # Replace marker with floor tile

        #calculate pixel coordinates centered inside tiles
        self.player_x = player_col * TILE_SIZE + (TILE_SIZE // 2)
        self.player_y = player_row * TILE_SIZE + (TILE_SIZE // 2)
        
        self.enemy_x = enemy_col * TILE_SIZE + (TILE_SIZE // 2)
        self.enemy_y = enemy_row * TILE_SIZE + (TILE_SIZE // 2)

    def get_camera_pos(self, screen_w, screen_h):
        #Calculates camera coordinates clamped strictly within map bounds.
        #find which tile the player is currently on
        p_row = max(0, min(int(self.player_y // TILE_SIZE), len(self.tile_map) - 1))
        p_col = max(0, min(int(self.player_x // TILE_SIZE), len(self.tile_map[0]) - 1))

        #Raycast left and right from player postion to find map boundaries
        left_c = p_col
        while left_c > 0 and self.tile_map[p_row][left_c - 1] is not None:
            left_c -= 1
        right_c = p_col
        while right_c < len(self.tile_map[0]) - 1 and self.tile_map[p_row][right_c + 1] is not None:
            right_c += 1

        top_r = p_row
        while top_r > 0 and self.tile_map[top_r - 1][p_col] is not None:
            top_r -= 1
        bottom_r = p_row
        while bottom_r < len(self.tile_map) - 1 and self.tile_map[bottom_r + 1][p_col] is not None:
            bottom_r += 1

        min_x = left_c * TILE_SIZE
        max_x = (right_c + 1) * TILE_SIZE
        min_y = top_r * TILE_SIZE
        max_y = (bottom_r + 1) * TILE_SIZE
        #center camera if area is smaller than screen, otherwise clamp to player position
        if max_x - min_x <= screen_w:
            cam_x = min_x - (screen_w - (max_x - min_x)) / 2
        else:
            cam_x = max(min_x, min(self.player_x - screen_w / 2, max_x - screen_w))

        if max_y - min_y <= screen_h:
            cam_y = min_y - (screen_h - (max_y - min_y)) / 2
        else:
            cam_y = max(min_y, min(self.player_y - screen_h / 2, max_y - screen_h))

        return cam_x, cam_y

    def check_collision(self, next_x, next_y, object_size=20):
        half = object_size / 2 #caculate bounding box edges for the given position
        p_left = next_x - half
        p_right = next_x + half
        p_top = next_y - half
        p_bottom = next_y + half
        #Get the range of tiles that the bounding box overlaps
        min_col = int(p_left // TILE_SIZE)
        max_col = int(p_right // TILE_SIZE)
        min_row = int(p_top // TILE_SIZE)
        max_row = int(p_bottom // TILE_SIZE)

        #Loop through touched tiles and check if any are solid walls or out of bounds
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                if r < 0 or r >= len(self.tile_map) or c < 0 or c >= len(self.tile_map[0]):
                    return True #Out of map bounds, treat as collision
                
                val = self.tile_map[r][c]
                if val is None or val in SOLID_TILES:
                    return True #Hit a wall
        return False #no collision detected

    def check_enemy_wall_collision(self, next_x, next_y):
        #Helper to run standard collision check using the enemy's size
        return self.check_collision(next_x, next_y, self.enemy_size)

    def update_enemy(self):

        #this prevents enemy movement if in question or while stunned
        if self.in_question_mode or self.enemy_stun_timer > 0:
            return
        # the enemy only moves if not touching player
        if self.check_enemy_hit():
            return
        # this moves the enemy towards the player
        # the calculation for the distance between the enemy and player
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        # distance formula
        dist = (dx**2 + dy**2) ** 0.5

        if dist != 0:
            # Calculate next positions
            next_ex = self.enemy_x + (dx / dist) * self.enemy_speed
            next_ey = self.enemy_y + (dy / dist) * self.enemy_speed
            
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



    def drawing_ofplayer_health(self):
        #Renders the full, half, and empty heart sprites on top left of the screen based on  the players health.
        start_x = 25  # Fixed left offset from screen
        start_y = 25  # Fixed top offset from screen 
        spacing = 35  # the gap spacing between each heart 

        # this loops through the maximum health capacity to check each heart slot
        for i in range(self.max_health):
            #  this calculates how much remaining health belongs to this specific heart slot (index i)
            container_hp = self.player_health - i

            # If the remaining value is 1 or higher, draw the full heart sprite
            if container_hp >= 1.0:
                sprite = self.img_full
            # If the remaining value is exactly 0.5, draw a half heart sprite
            elif container_hp == 0.5:
                sprite = self.img_half
            # If the remaining value is 0 or less, draw an empty heart sprite
            else:
                sprite = self.img_empty

            # this Calculates the screens horizontal position for this heart
            current_x = start_x + (i * spacing)

            # this Draws the chosen heart sprite onto the screen
            self.screen.blit(sprite, (current_x, start_y))


    def draw_dialogue_box(self):
        #Renders dialogue box attached at the bottom center of the screen with animated typewriter text, option prompts, and a countdown timer
        screen_w, screen_h = self.screen.get_size()

        # the Box dimensions and positioning at the bottom center of the screen
        box_w, box_h = 600, 160
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h - 40

        #this draws the main black dialogue box
        pygame.draw.rect(self.screen, (0, 0, 0), 
                         (box_x, box_y, box_w, box_h))
        #this draws the white border
        pygame.draw.rect(self.screen, (255, 255, 255), 
                         (box_x, box_y, box_w, box_h), 5)

        #this slices the string up to create the typing effect
        visible_text = self.dialogue_full_text[: int(self.typewriter_index)]
        text_surface = self.font.render(visible_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (box_x + 25, box_y + 25))

        #this renders the response option keys once the question text finishes typing
        if self.typewriter_index >= len(self.dialogue_full_text):
            options_surface = self.subfont.render(
                "[O] YES          [X] NO", True, (255, 255, 255)
            )
            self.screen.blit(options_surface, (box_x + 25, box_y + 75))

        # this calculates and renders the remaining 5 second countdown timer in yellow text
        time_left_sec = max(0.0, self.question_timer / 60.0)
        timer_surface = self.subfont.render(
            f"TIME: {time_left_sec:.1f}s", True, (255, 255, 0)
        )
        self.screen.blit(timer_surface, (box_x + box_w - 150, box_y + box_h - 35))

    def run_game(self):
        running = True
        while running:
            #event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False


                #this Handles player answer inputs when paused inside dialogue mode
                if self.in_question_mode and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y or event.key == pygame.K_o:
                        #if the anwser is correct, negate all damage and stun the enemy for 3s, which then resumes the play
                        self.in_question_mode = False
                        self.enemy_stun_timer = 180  # 3 seconds stun at 60 FPS
                        self.hit_cooldown = self.max_hit_cooldown
                    elif event.key == pygame.K_n or event.key == pygame.K_x:#elif is short for else if on golly100%
                        #When the anwser is wrong the player takes half a heart of damage (0.5)
                        self.player_health -= 0.5
                        self.in_question_mode = False
                        self.hit_cooldown = self.max_hit_cooldown

            # Controls
            if not self.in_question_mode:#this completely disables the movement while in question mode
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

                #Update position with collisions
                if dx != 0 and not self.check_collision(
                    self.player_x + dx, self.player_y
                ):
                    self.player_x += dx
                if dy != 0 and not self.check_collision(
                    self.player_x, self.player_y + dy
                ):
                    self.player_y += dy

            #enemy stun duration timer
            if self.enemy_stun_timer > 0:
                self.enemy_stun_timer -= 1

            # this updates the enemy position
            self.update_enemy()

            # the health and iframe Cooldown setup
            # iframe timer every frame tick
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1

            #this checks enemy collision to trigger question mode if not currently in iframes or active question
            if (
                self.check_enemy_hit()
                and self.hit_cooldown == 0
                and not self.in_question_mode
                and self.enemy_stun_timer == 0
            ):
                self.in_question_mode = True
                self.question_timer = 300  # 5 Seconds at 60 FPS (300 ticks)
                self.typewriter_index = 0  # the reset text animation index

            #the question timer and typewriter text update logic while in question mode
            if self.in_question_mode:
                # this increments the text typewriter character counter, 1 character added every 2 frames
                if self.typewriter_index < len(self.dialogue_full_text):
                    self.typewriter_index += 0.5

                # the 5 second timer
                self.question_timer -= 1
                if self.question_timer <= 0:
                    #if the player takes longer than 5 seconds, deal a full heart
                    self.player_health -= 1.0
                    self.in_question_mode = False
                    self.hit_cooldown = self.max_hit_cooldown


            #Render the Frame
            self.screen.fill((240, 240, 240))  #Background
            screen_w, screen_h = self.screen.get_size()
            
            #Recalculate camera offset based on updated player position
            cam_x, cam_y = self.get_camera_pos(screen_w, screen_h)

            #Draw map relative to camera
            for r_idx, row in enumerate(self.tile_map):
                for c_idx, tile_id in enumerate(row):
                    if tile_id is not None and tile_id in COLOR_MAP:
                        world_x = c_idx * TILE_SIZE
                        world_y = r_idx * TILE_SIZE

                        #Convert world positions to screen relative coordinates
                        screen_x = world_x - cam_x
                        screen_y = world_y - cam_y
                        
                        #Only draw tiles that are actually visible on the screen to save processing time
                        if -TILE_SIZE <= screen_x <= screen_w and -TILE_SIZE <= screen_y <= screen_h:
                            tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                            pygame.draw.rect(self.screen, COLOR_MAP[tile_id], tile_rect)

            #draw player at screen center
            player_screen_x = self.player_x - cam_x
            player_screen_y = self.player_y - cam_y
            half_p = self.player_size / 2
            player_rect = pygame.Rect(
                player_screen_x - half_p,
                player_screen_y - half_p,
                self.player_size,
                self.player_size,
            )
            pygame.draw.rect(
                self.screen, (146, 238, 255), player_rect
            )  

            #this positions the enemy relative to camera
            half_e = self.enemy_size / 2
            ex1 = (self.enemy_x - cam_x) - half_e
            ey1 = (self.enemy_y - cam_y) - half_e
            enemy_rect = pygame.Rect(
                ex1, ey1, self.enemy_size, self.enemy_size
            )

            #this Draws the enemy as yellow if currently stunned if not jus regular blue
            enemy_color = (255, 215, 0) if self.enemy_stun_timer > 0 else (5, 0, 139)
             
            pygame.draw.rect(self.screen, enemy_color, enemy_rect) 

            #this Displays STUNNED! text marker above enemy when the enemy is in a 3 second stun state
            if self.enemy_stun_timer > 0:
                stun_surface = self.font.render("STUNNED!", True, (255, 140, 0))
                stun_rect = stun_surface.get_rect(center=(ex1 + half_e, ey1 - 15))
                self.screen.blit(stun_surface, stun_rect)


            #this displays "HIT!
            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(
                    center=(player_screen_x, player_screen_y - 30)
                )
                self.screen.blit(text_surface, text_rect)

            self.drawing_ofplayer_health() #Draw HUD elements over the world view

            #this renders the dialogue box when question state is triggered
            if self.in_question_mode:
                self.draw_dialogue_box()
            #Refresh display and throttle frame rate to 60 FPS
            pygame.display.flip()
            self.clock.tick(60)  #Lock to 60 FPS

        pygame.quit() #Clean exit when loop breaks
        sys.exit()

if __name__ == "__main__":
    App()
