import sys
import pygame
import csv

TILE_SIZE = 40

COLOR_MAP = {
    '0': (255, 255, 255),
    '1': (80, 80, 80),
    '2': (100, 150, 220),
    '3': (40, 40, 40),
    '4': (240, 180, 130),
    '5': (140, 140, 140),
    '6': (200, 200, 200),
    "48": (40, 40, 40),  # Science Classroom 48 Left Door
    "49": (40, 40, 40),  # Science Classroom 49 Right Door
    "50": (40, 40, 40),  # Classroom 50 Left Door
    "51": (40, 40, 40),  # Classroom 51 Right Door
    "52": (40, 40, 40),  # Classroom 52 Left Door
    "53": (40, 40, 40),  # Classroom 53 Right Door
    "54": (40, 40, 40),  # Classroom 54 Left Door
    "55": (40, 40, 40),  # Classroom 55 Right Door
    "56": (40, 40, 40),  # Science Classroom 56 Left Door
    "57": (40, 40, 40),  # Science Classroom 57 Right Door
    "58": (40, 40, 40),  # Science Classroom 58 Left Door
    "59": (40, 40, 40),  # Science Classroom 59 Right Door
    "60": (40, 40, 40),  # Science Classroom 60 Left Door
    "61": (40, 40, 40),  # Science Classroom 61 Right Door
    "62": (40, 40, 40),  # Food Room 62 Door
    "63": (40, 40, 40),  # Food Room 63 Door
    "64": (40, 40, 40),  # Food Room 64 Door
    "65": (40, 40, 40),  # Food Room 65 Door
    "66": (40, 40, 40),  # Food Room 66 Door
    "67": (40, 40, 40),  # Food Room 67 Door
    "68": (40, 40, 40),  # Food Room 68 Door
    "69": (40, 40, 40),  # Food Room 69 Door
}

SOLID_TILES = {'0','1', '2', '3', '4'}
Door_Tiles = {'48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69'}


class App:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Northcote K-block demon hunters")
        self.clock = pygame.time.Clock()

        #Load the map and set spawn positions
        self.current_map = "MAP - Level 3 (8).csv"
        self.defeated_rooms = set() # Remembers cleared classroom files
        self.locked_message_timer = 0

        #player stuff
        self.speed = 5
        self.player_size = 20
        self.player_render_size = 65 #sprite
        self.max_health = 3
        self.player_health = 3

        self.hit_cooldown = 0
        self.max_hit_cooldown = 60

        self.tile_map = []
        self.load_map(self.current_map)
        
         #Enemy movement setup
        self.enemy_size = 20
        self.enemy_render_size = 90 #sprite
        self.enemy_speed = 5
        
        self.enemy_max_health = 100
        self.enemy_health = 100

         #Load and scale sprites
        self.player_img = pygame.image.load("Boii.webp").convert_alpha() 
        self.player_img = pygame.transform.scale(self.player_img, (self.player_render_size, self.player_render_size))
        
        self.enemy_img = pygame.image.load("unnamed.png").convert_alpha()
        self.enemy_img = pygame.transform.scale(self.enemy_img, (self.enemy_render_size, self.enemy_render_size))
        
        self.enemy_active = False
        self.set_spawns_from_map()
       

        #Player attack setup
        self.attack_range = 30
        self.attack_damage = 5
        self.max_stun_hits = 3

        self.enemy_stun_hits = 0
        self.enemy_knockback = 150
        self.knockback_duration = 15

        self.knockback_frames = 0
        self.knockback_step_x = 0
        self.knockback_step_y = 0

        #stun setup
        self.enemy_stun_timer = 0 # the counter in frames (180 frames = 3 seconds at 60 FPS)
        self.in_question_mode = False # the flag to pause movement and display the dialogue overlay
        self.question_timer = 0    # the timer for answering

        self.typewriter_index = 0   # the character counter for animating the question text letter by letter
        self.dialogue_full_text = "yo g, Are apples red?" # the full text string for the dialogue box

        #Fonts
        self.font = pygame.font.SysFont("Courier New", 22, bold=True)
        self.subfont = pygame.font.SysFont("Courier New", 18, bold=True)

        #Heart sprites
        self.img_full = pygame.image.load("full_heart.png").convert_alpha()
        self.img_half = pygame.image.load("half_heart.png").convert_alpha()
        self.img_empty = pygame.image.load("empty_heart.png").convert_alpha()

        heart_size = (24, 24)#scales the heart sprites to 24x24 for the screen
        self.img_full = pygame.transform.scale(self.img_full, heart_size)
        self.img_half = pygame.transform.scale(self.img_half, heart_size)
        self.img_empty = pygame.transform.scale(self.img_empty, heart_size)


        self.run_game()

    def load_map(self, filename):

        #Load map tiles and spawn markers from CSV
        self.tile_map = []
        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    map_row = []
                    for col in row:
                        val = col.strip() #clean up empty cells

                        if val and val.lower() != 'nan': # empty space
                            try:
                                val = str(int(float(val))) #convert floating numbers to clean integers
                            except ValueError:
                                val = val.upper() # Keep string markers like 'P' or 'E'
                        else:
                            val = None # Empty space
                        map_row.append(val)
                    self.tile_map.append(map_row)

        except FileNotFoundError:
            print(f"Error: {filename} not found.")

    def set_spawns_from_map(self):

        #Default spawn positions
        player_col, player_row = 7, 0

        has_enemy_spawn = False
        enemy_col, enemy_row = 0, 0

        for r_idx, row in enumerate(self.tile_map):# Scan map for spawn letters 'P' and 'E'
            for c_idx, tile in enumerate(row):
                if tile == 'P': #Player spawn
                    player_col, player_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = '5' # Replace marker with floor tile
                elif tile == 'E': #Enemy spawn
                    has_enemy_spawn = True
                    enemy_col, enemy_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = '5' # Replace marker with floor tile

        self.player_x = player_col * TILE_SIZE + (TILE_SIZE // 2)
        self.player_y = player_row * TILE_SIZE + (TILE_SIZE // 2)

        if has_enemy_spawn and self.current_map not in self.defeated_rooms:
            self.enemy_active = True
            self.enemy_health = self.enemy_max_health
            self.enemy_x = enemy_col * TILE_SIZE + (TILE_SIZE // 2)
            self.enemy_y = enemy_row * TILE_SIZE + (TILE_SIZE // 2)
        else:
            self.enemy_active = False

    def change_room(self, target_map_file, spawn_col, spawn_row):

        self.current_map = target_map_file 
        self.load_map(target_map_file)  #swaps active CSV map
    
        self.player_x = spawn_col * TILE_SIZE + (TILE_SIZE // 2)
        self.player_y = spawn_row * TILE_SIZE + (TILE_SIZE // 2)

        has_enemy_spawn = False #same as set_spawns_from_map
        enemy_col, enemy_row = 0, 0
        for r_idx, row in enumerate(self.tile_map):
            for c_idx, tile in enumerate(row):
                if tile == "E": #player already placed, so we only need to check for enemy spawn
                    has_enemy_spawn = True
                    enemy_col, enemy_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = "5"

        if has_enemy_spawn and self.current_map not in self.defeated_rooms:
            self.enemy_active = True
            self.enemy_health = self.enemy_max_health
            self.enemy_x = enemy_col * TILE_SIZE + (TILE_SIZE // 2)
            self.enemy_y = enemy_row * TILE_SIZE + (TILE_SIZE // 2)
        else:
            self.enemy_active = False

    def get_camera_pos(self, screen_w, screen_h):
        if not self.tile_map or not self.tile_map[0]: #Empty map, return default camera position
            return 0, 0 
    
        #Keep the camera within the map
        p_row = max(0, min(int(self.player_y // TILE_SIZE), len(self.tile_map) - 1)) #max(0, min(...)) ensures the row index is within bounds
        p_col = max(0, min(int(self.player_x // TILE_SIZE), len(self.tile_map[0]) - 1)) #why -1? because the index starts at 0, so the last index is length - 1

        left_c = p_col #find the leftmost non-empty tile
        while left_c > 0 and self.tile_map[p_row][left_c - 1] is not None: #camera can move left as long as the tile to the left is not None
            left_c -= 1 # moves left one tile at a time

        right_c = p_col
        while right_c < len(self.tile_map[0]) - 1 and self.tile_map[p_row][right_c + 1] is not None: #check the tile below the current one
            right_c += 1 

        top_r = p_row 
        while top_r > 0 and self.tile_map[top_r - 1][p_col] is not None: 
            top_r -= 1

        bottom_r = p_row
        while bottom_r < len(self.tile_map) - 1 and self.tile_map[bottom_r + 1][p_col] is not None: 
            bottom_r += 1

        min_x = left_c * TILE_SIZE #the camera position is in pixels
        max_x = (right_c + 1) * TILE_SIZE #plus 1 so that the camera includes the entire rightmost tile, not just its left edge
        min_y = top_r * TILE_SIZE
        max_y = (bottom_r + 1) * TILE_SIZE

        if max_x - min_x <= screen_w: #when the map is smaller than the screen, center the camera on the map
            cam_x = min_x - (screen_w - (max_x - min_x)) / 2 #/2 to center the camera on the map
        else:
            cam_x = max(min_x, min(self.player_x - screen_w / 2, max_x - screen_w)) #follow player

        if max_y - min_y <= screen_h:
            cam_y = min_y - (screen_h - (max_y - min_y)) / 2
        else:
            cam_y = max(min_y, min(self.player_y - screen_h / 2, max_y - screen_h))
        return cam_x, cam_y

    def check_collision(self, next_x, next_y, object_size=20):

        # The position is the character's center, so center its rectangle there.
        character_rect = pygame.Rect(0, 0, object_size, object_size)
        character_rect.center = (round(next_x), round(next_y))

        # Only inspect tiles near the character, not the entire map.
        min_col = character_rect.left // TILE_SIZE
        max_col = (character_rect.right - 1) // TILE_SIZE
        min_row = character_rect.top // TILE_SIZE
        max_row = (character_rect.bottom - 1) // TILE_SIZE

        #r is the row index, c is the column index
        for r in range(min_row, max_row + 1): 
            for c in range(min_col, max_col + 1):
                if r < 0 or r >= len(self.tile_map) or c < 0 or c >= len(self.tile_map[r]):
                    return True # Outside the map
                tile = self.tile_map[r][c]

                if tile is None or tile in SOLID_TILES: 
                    wall_rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE) 
                    if character_rect.colliderect(wall_rect): #if overlapping, then collision detected
                        return True
        return False #no collision detected

    def check_enemy_wall_collision(self, next_x, next_y):
        return self.check_collision(next_x, next_y, self.enemy_size) #return to same collision check

    def update_enemy(self):

        #Pause enemy movement during questions, stuns and knockback
        if (
            not self.enemy_active 
            or self.in_question_mode
            or self.enemy_stun_timer > 0
            or self.knockback_frames > 0
        ):
            return 
        if self.check_enemy_hit():
            return 
        
        dx = self.player_x - self.enemy_x #difference coordinates between the player and the enemy
        dy = self.player_y - self.enemy_y 
        dist = (dx**2 + dy**2) ** 0.5 #** 0.5 is the same as taking the square root

        if dist != 0:
            next_ex = self.enemy_x + (dx / dist) * self.enemy_speed
            next_ey = self.enemy_y + (dy / dist) * self.enemy_speed

            if not self.check_enemy_wall_collision(next_ex, self.enemy_y):
                self.enemy_x = next_ex

            if not self.check_enemy_wall_collision(self.enemy_x, next_ey):
                self.enemy_y = next_ey

    def check_enemy_hit(self):
        if not self.enemy_active:
            return False

        # The stored positions are centers, not top-left corners.
        player_rect = pygame.Rect(0, 0, self.player_size, self.player_size)
        player_rect.center = (round(self.player_x), round(self.player_y))

        enemy_rect = pygame.Rect(0, 0, self.enemy_size, self.enemy_size)
        enemy_rect.center = (round(self.enemy_x), round(self.enemy_y))
        return player_rect.colliderect(enemy_rect)

    def check_enemy_attack_range(self):

        #Check player attack distance
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        distance = (dx**2 + dy**2) ** 0.5
        return distance <= self.attack_range

    def knockback_enemy(self):

        #Set knockback direction away from the player
        dx = self.enemy_x - self.player_x
        dy = self.enemy_y - self.player_y
        distance = (dx**2 + dy**2) ** 0.5

        if distance == 0:
            dx = 1
            dy = 0
            distance = 1
        direction_x = dx / distance
        direction_y = dy / distance

        self.knockback_step_x = direction_x * (self.enemy_knockback / self.knockback_duration)
        self.knockback_step_y = direction_y * (self.enemy_knockback / self.knockback_duration)
        self.knockback_frames = self.knockback_duration

    def update_enemy_knockback(self):

        #Move the enemy smoothly during knockback
        if self.knockback_frames <= 0:
            return
        
        steps = max(1, int(max(abs(self.knockback_step_x), abs(self.knockback_step_y))) + 1)

        move_x = self.knockback_step_x / steps
        move_y = self.knockback_step_y / steps

        for i in range(steps):
            next_x = self.enemy_x + move_x
            next_y = self.enemy_y + move_y
            if not self.check_enemy_wall_collision(next_x, self.enemy_y):
                self.enemy_x = next_x
            if not self.check_enemy_wall_collision(self.enemy_x, next_y):
                self.enemy_y = next_y
    
        self.knockback_frames -= 1

    def drawing_ofplayer_health(self):
        start_x = 25 # Fixed left offset from screen
        start_y = 25 # Fixed top offset from screen
        spacing = 35 # the gap spacing between each heart

        for i in range(self.max_health):
            container_hp = self.player_health - i
            if container_hp >= 1.0:
                sprite = self.img_full
            elif container_hp == 0.5:
                sprite = self.img_half
            else:
                sprite = self.img_empty

            current_x = start_x + (i * spacing)
            self.screen.blit(sprite, (current_x, start_y)) #Draw the heart sprite at the calculated position

    def drawing_ofenemy_health(self):
        if not self.enemy_active:
            return

        #Draw enemy health bar
        screen_w, screen_h = self.screen.get_size() #get_size() gets screen width and height
        bar_width = 400
        bar_height = 20
        bar_x = (screen_w - bar_width) // 2 #center the bar horizontally
        bar_y = 25 #25 pixels from the top of the screen

        health_ratio = self.enemy_health / self.enemy_max_health
        current_bar_width = bar_width * health_ratio

        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (200, 40, 40), (bar_x, bar_y, current_bar_width, bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 
                         2) #2 border thickness

    def draw_dialogue_box(self):

        #Draw question box, answers and timer
        screen_w, screen_h = self.screen.get_size() #get_size gets screen width and height

        box_w, box_h = 600, 160
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h - 40

        pygame.draw.rect(self.screen, (0, 0, 0),
                        (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, (255, 255, 255),
                        (box_x, box_y, box_w, box_h), 5)

        #slices the string to create a typewriter effect
        visible_text = self.dialogue_full_text[: int(self.typewriter_index)] 
        
        text_surface = self.font.render(visible_text, True, (255, 255, 255))

        self.screen.blit(text_surface, (box_x + 25, box_y + 25))

        if self.typewriter_index >= len(self.dialogue_full_text):
            options_surface = self.subfont.render(
                "[O] YES     [X] NO", True, (255, 255, 255)
            )
            self.screen.blit(options_surface, (box_x + 25, box_y + 75))

        time_left_sec = max(0.0, self.question_timer / 60.0)
        timer_surface = self.subfont.render(
            f"TIME: {time_left_sec:.1f}s", True, (255, 255, 0)
        )

        self.screen.blit(timer_surface, (box_x + box_w - 150, box_y + box_h - 35))

    def player_respawnyes(self):
    #this return to the original map and its P spawn marker
        self.current_map = "MAP - Level 3 (8).csv"
        self.load_map(self.current_map)
        self.set_spawns_from_map()
    #sets dthe player back to full health
        self.player_health = self.max_health
    #everythin below here clears unfinished stuf
        self.in_question_mode = False
        self.question_timer = 0
        self.typewriter_index = 0
        self.hit_cooldown = self.max_hit_cooldown
        self.enemy_stun_timer = 0
        self.enemy_stun_hits = 0
        self.knockback_frames = 0
        self.knockback_step_x = 0
        self.knockback_step_y = 0
        self.locked_message_timer = 0

    def death_screen(self):
            screen_w, screen_h = self.screen.get_size()
            message = self.font.render("U acc Suck, Press R", True, (255, 255, 255))
            self.screen.blit(
                message,
                message.get_rect(center=(screen_w // 2, screen_h // 2))
            )
            pygame.display.flip()
            self.clock.tick(60)


    def run_game(self):
        running = True
        while running:
            #Handle keyboard and quit events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

                  #checks if player is dead and if r is pressed, if is pressed then call player_respawnyes
                if self.player_health <= 0:
                  if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                      self.player_respawnyes()
                    

                #Handle question answers
                if self.in_question_mode and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y or event.key == pygame.K_o:
                        self.in_question_mode = False
                        self.enemy_stun_timer = 180 # 3 seconds stun at 60 FPS
                        self.enemy_stun_hits = 0 #resets the successful attack counter for the new stun
                        self.hit_cooldown = self.max_hit_cooldown
                    elif event.key == pygame.K_n or event.key == pygame.K_x:#elif is short for else if on golly100%
                        self.player_health -= 0.5
                        self.in_question_mode = False
                        self.hit_cooldown = self.max_hit_cooldown

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: 
                    if (self.enemy_active and
                        self.enemy_stun_timer > 0 and
                        self.knockback_frames == 0 and # added This so that it prevents the player from landing another punch while the enemy is still being pushed backward
                        self.check_enemy_attack_range() and
                        self.enemy_stun_hits < self.max_stun_hits):

                        self.enemy_health = max(0, self.enemy_health - self.attack_damage)

                        self.enemy_stun_hits += 1
                        self.knockback_enemy()

                        if self.enemy_health <= 0:
                            self.enemy_active = False #room is cleared of enemies
                            self.defeated_rooms.add(self.current_map)

                        if self.enemy_stun_hits >= self.max_stun_hits:
                            self.enemy_stun_timer = 0


            # player movement
            if not self.in_question_mode:#this completely disables the movement while in question mode
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

                if dx != 0 and not self.check_collision(
                    self.player_x + dx, self.player_y
                ):
                    self.player_x += dx
                if dy != 0 and not self.check_collision(
                    self.player_x, self.player_y + dy
                ):
                    self.player_y += dy

                #Door transisiton and lock
                current_col = int(self.player_x // TILE_SIZE)
                current_row = int(self.player_y // TILE_SIZE)

                if 0 <= current_row < len(self.tile_map) and 0 <= current_col < len( #in bounds of map
                    self.tile_map[0] 
                ):
                    tile_val = self.tile_map[current_row][current_col]

            if tile_val in Door_Tiles:
                        if (
                            self.current_map != "MAP - Level 3 (8).csv"
                            and self.enemy_active
                        ):
                            self.locked_message_timer = 90
                            self.player_y -= TILE_SIZE // 2 #move the player back to prevent them from getting stuck in the door tile
                        else:

                            if tile_val == "48": #door tile
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science 1 Classroom 48_49.csv",
                                        spawn_col=4, #spawn position in the new room
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv", #return to the main map
                                        spawn_col=9,#spawn position in the main map
                                        spawn_row=13,
                                    ) 
                            #code is repeated for each door tile, with different spawn positions for each room again and again till 69
                            elif tile_val == "49":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science 1 Classroom 48_49.csv",
                                        spawn_col=31,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=15,
                                        spawn_row=13,
                                    )

                            elif tile_val == "50":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Math classroom Test 50_51.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=18,
                                        spawn_row=13,
                                    )

                            elif tile_val == "51":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Math classroom Test 50_51.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=24,
                                        spawn_row=13,
                                    )

                            elif tile_val == "52":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 52_53.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=27,
                                        spawn_row=13,
                                    )

                            elif tile_val == "53":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 52_53.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=33,
                                        spawn_row=13,
                                    )

                            elif tile_val == "54":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 54_55.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=36,
                                        spawn_row=13,
                                    )

                            elif tile_val == "55":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 54_55.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=42,
                                        spawn_row=13,
                                    )

                            elif tile_val == "56":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 56_57.csv",
                                        spawn_col=3,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=16,
                                        spawn_row=20,
                                    )

                            elif tile_val == "57":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 56_57.csv",
                                        spawn_col=28,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=23,
                                        spawn_row=20,
                                    )

                            elif tile_val == "58":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 58_59.csv",
                                        spawn_col=3,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=27,
                                        spawn_row=20,
                                    )

                            elif tile_val == "59":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 58_59.csv",
                                        spawn_col=28,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=33,
                                        spawn_row=20,
                                    )

                            elif tile_val == "60":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 60_61.csv",
                                        spawn_col=3,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=37,
                                        spawn_row=20,
                                    )

                            elif tile_val == "61":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 60_61.csv",
                                        spawn_col=28,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=45,
                                        spawn_row=20,
                                    )

                            elif tile_val == "62":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 62_63 (4).csv",
                                        spawn_col=6,
                                        spawn_row=8,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=70,
                                        spawn_row=28,
                                    )

                            elif tile_val == "63":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 62_63 (4).csv",
                                        spawn_col=18,
                                        spawn_row=22,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=82,
                                        spawn_row=44,
                                    )

                            elif tile_val == "64":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Copy of Food room 62_63 (1).csv",
                                        spawn_col=15,
                                        spawn_row=27,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=89,
                                        spawn_row=40,
                                    )

                            elif tile_val == "65":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Copy of Food room 62_63 (1).csv",
                                        spawn_col=34,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=101,
                                        spawn_row=15,
                                    )

                            elif tile_val == "66":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 66_67.csv",
                                        spawn_col=16,
                                        spawn_row=4,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=81,
                                        spawn_row=61,
                                    )

                            elif tile_val == "67":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 66_67.csv",
                                        spawn_col=16,
                                        spawn_row=23,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=81,
                                        spawn_row=72,
                                    )

                            elif tile_val == "68":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 68_69.csv",
                                        spawn_col=20,
                                        spawn_row=4,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=90,
                                        spawn_row=61,
                                    )

                            elif tile_val == "69":
                                if self.current_map == "MAP - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 68_69.csv",
                                        spawn_col=20,
                                        spawn_row=27,
                                    )
                                else:
                                    self.change_room(
                                        "MAP - Level 3 (8).csv",
                                        spawn_col=90,
                                        spawn_row=77,
                                    ) #End of room change code

            #Update stun and knockback timers
            if self.enemy_stun_timer > 0:
                self.enemy_stun_timer -= 1

            self.update_enemy_knockback() #updates the enemy knockback animation once per frame
            self.update_enemy()

            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1

            #Start a question when the enemy touches the player
            if (
                self.enemy_active and
                self.check_enemy_hit()
                and self.hit_cooldown == 0
                and not self.in_question_mode
                and self.enemy_stun_timer == 0
            ):
                self.in_question_mode = True
                self.question_timer = 300 # 5 Seconds at 60 FPS (300 ticks)
                self.typewriter_index = 0 # the reset text animation index

            #Update question text and timer
            if self.in_question_mode:
                if self.typewriter_index < len(self.dialogue_full_text):
                    self.typewriter_index += 0.5
                self.question_timer -= 1
                if self.question_timer <= 0:
                    self.player_health -= 1.0
                    self.in_question_mode = False
                    self.hit_cooldown = self.max_hit_cooldown


            #if the player health is 0 or les then call the deathscreenfucntion
            if self.player_health <= 0:
                self.death_screen()
                continue#i use this to skip

            #Render the game
            self.screen.fill((240, 240, 240)) #Background

            screen_w, screen_h = self.screen.get_size()

            #Get the camera position based on the player's position and the map boundaries
            cam_x, cam_y = self.get_camera_pos(screen_w, screen_h) 

            #Draw the map
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

            #Draw the player
            player_screen_x = self.player_x - cam_x
            player_screen_y = self.player_y - cam_y
            half_p_render = self.player_render_size / 2

            player_render_rect = pygame.Rect(
                player_screen_x - half_p_render,
                player_screen_y - half_p_render,
                self.player_render_size,
                self.player_render_size,
            )
            # Method draws image on player
            self.screen.blit(self.player_img, player_render_rect.topleft)

            #Draw the enemy
            if self.enemy_active:
                half_e_render = self.enemy_render_size / 2
                ex1 = (self.enemy_x - cam_x) - half_e_render
                ey1 = (self.enemy_y - cam_y) - half_e_render
                enemy_render_rect = pygame.Rect(
                    ex1, ey1, self.enemy_render_size, self.enemy_render_size
                )
                # Method draws image on enemy
                self.screen.blit(self.enemy_img, enemy_render_rect.topleft)

            #Show stun indicator
            if self.enemy_stun_timer > 0:
                stun_surface = self.font.render("STUNNED!", True, (255, 140, 0))
                stun_rect = stun_surface.get_rect(center=(ex1 + half_e_render, ey1 - 15))
                self.screen.blit(stun_surface, stun_rect)

            #Show contact indicator
            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(
                    center=(player_screen_x, player_screen_y - 30)
                )
                self.screen.blit(text_surface, text_rect)

            self.drawing_ofplayer_health() #Draw HUD elements over the world view
            self.drawing_ofenemy_health() #Draw enemy health bar over the world view

            if self.locked_message_timer > 0:
                self.locked_message_timer -= (1)
                msg_surface = self.font.render("DOOR IS LOCKED! DEFEAT THE DEMON FIRST!", True, (0, 0, 0),  )
                msg_rect = msg_surface.get_rect(center=(
                        screen_w // 2, screen_h // 2 - 100, )  # Position the message above the player
                )
                pygame.draw.rect(
                    self.screen, 
                    (255, 0, 0),
                    msg_rect.inflate(
                        20, 10),  # Red background rectangle
                )
                self.screen.blit(msg_surface, msg_rect)

            
            #Show the active question
            if self.in_question_mode:
                self.draw_dialogue_box()
            pygame.display.flip()
            self.clock.tick(60) #Lock to 60 FPS
        pygame.quit() #Clean exit when loop breaks
        sys.exit()

if __name__ == "__main__":
    App() 
