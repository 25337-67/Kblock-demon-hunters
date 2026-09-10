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


        # the playble character health setup   
        # the Maximum health points capacity
        self.max_health = 3
        # the current health remaining for the player
        self.player_health = 3
        # the cooldown to prevent losing all 3 hearts instantly when coming into contact with the enemy
        self.hit_cooldown = 0
        # Iframe duration 60 frames = 1 second buffer at 60 FPS
        self.max_hit_cooldown = 60


        # World Position of the player
        self.player_x = 0
        self.player_y = 0

        # da enemy setup
        # this is the dimensions of the enemy collision box 20x20 pixels square
        self.enemy_size = 20
        # the movement step per frame in pixels moves 5 units to the player every tick
        self.enemy_speed = 5
        # Spawning position in world coordinates
        self.enemy_x = 300  # Starts 300 units to the right of origin
        self.enemy_y = 200  # Starts 200 units below origin

        # the state tracking for the 3 second stun on the enemy after a correct answer
        self.enemy_stun_timer = 0  # the counter in frames (180 frames = 3 seconds at 60 FPS)

        # the State tracking for question popup 
        self.in_question_mode = False  # the flag to pause movement and display the dialogue overlay
        self.question_timer = 0        # the timer in frames for answering (300 frames = 5 seconds)
        self.typewriter_index = 0      # the character counter for animating the question text letter by letter
        self.dialogue_full_text = "yo g, Are apples red?"  # the full text string for the dialogue box

        # the font setup for the hit text marker
        self.font = pygame.font.SysFont("Arial", 24, bold=True)

        # the fonts are styled for the Retro dialogue box 
        self.retro_font = pygame.font.SysFont("Courier New", 22, bold=True)
        self.retro_subfont = pygame.font.SysFont("Courier New", 18, bold=True)


        # Wall obstacles in World Coordinates: (x1, y1, x2, y2)
        self.walls_world = [
            (-100, -150, 100, -100),  # Top wall
            (150, -100, 200, 200),  # Right side pillar
        (-200, -150, -150, 150),
        ]

        # this loads the heart sprite images 
        self.img_full = pygame.image.load("full_heart.png").convert_alpha()
        self.img_half = pygame.image.load("half_heart.png").convert_alpha()
        self.img_empty = pygame.image.load("empty_heart.png").convert_alpha()

        # scales the heart sprites to 24x24 for the screen
        heart_size = (24, 24)
        self.img_full = pygame.transform.scale(self.img_full, heart_size)
        self.img_half = pygame.transform.scale(self.img_half, heart_size)
        self.img_empty = pygame.transform.scale(self.img_empty, heart_size)
        self.run_game()

    def check_collision(self, next_x, next_y):
        half_size = self.player_size / 2
        p_left = next_x - half_size
        p_right = next_x + half_size
        p_top = next_y - half_size
        p_bottom = next_y + half_size

        for wx1, wy1, wx2, wy2 in self.walls_world:
            # collision checks, If player is completely to the left, right, top, or bottom of wall, no collision.
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

        # this Prevents enemy movement if in question or while stunned
        if self.in_question_mode or self.enemy_stun_timer > 0:
            return
        # the enemy only moves if not touching player
        if self.check_enemy_hit():
            return
        # this moves the enemy towards da players main positions
        # the calculation for the distance vector components from enemy to player
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
        """
        Renders the full, half, and empty heart sprites on top left of the screen based on  the players health.
        
        """
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


    def draw_retro_dialogue_box(self):
        """
        Renders a Retro style dialogue box attached at the bottom center of the screen
        with animated typewriter text, option prompts, and a countdown timer
        """
        screen_w, screen_h = self.screen.get_size()

        # the Box dimensions and positioning at the bottom center of the screen
        box_w, box_h = 600, 160
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h - 40

        # this draws the main black dialogue box
        pygame.draw.rect(self.screen, (0, 0, 0), (box_x, box_y, box_w, box_h))
        # this Draws the double white border
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), 5)
        pygame.draw.rect(self.screen, (0, 0, 0), (box_x + 5, box_y + 5, box_w - 10, box_h - 10), 3)

        # this Slices the string up to the current typewriter index to create the typing effect
        visible_text = self.dialogue_full_text[: int(self.typewriter_index)]
        text_surface = self.retro_font.render(visible_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (box_x + 25, box_y + 25))

        #  this Renders the response option keys once the question text finishes typing
        if self.typewriter_index >= len(self.dialogue_full_text):
            options_surface = self.retro_subfont.render(
                "[O] YES          [X] NO", True, (255, 255, 255)
            )
            self.screen.blit(options_surface, (box_x + 25, box_y + 75))

        # this Calculates and render the remaining 5 second countdown timer in yellow text
        time_left_sec = max(0.0, self.question_timer / 60.0)
        timer_surface = self.retro_subfont.render(
            f"TIME: {time_left_sec:.1f}s", True, (255, 255, 0)
        )
        self.screen.blit(timer_surface, (box_x + box_w - 150, box_y + box_h - 35))

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


                # this Handles player answer inputs when paused inside dialogue mode
                if self.in_question_mode and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y or event.key == pygame.K_o:
                        # if the anwser is correct, Negate all damage and stun the enemy for 3s (180 frames), which then resumes the play
                        self.in_question_mode = False
                        self.enemy_stun_timer = 180  # 3 seconds stun at 60 FPS
                        self.hit_cooldown = self.max_hit_cooldown
                    elif event.key == pygame.K_n or event.key == pygame.K_x:#elif is short for else if on golly100%
                        # When the anwser is wrong the Player takes half a heart of damage (0.5)
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

                # Update Position with Collisions
                if dx != 0 and not self.check_collision(
                    self.player_x + dx, self.player_y
                ):
                    self.player_x += dx
                if dy != 0 and not self.check_collision(
                    self.player_x, self.player_y + dy
                ):
                    self.player_y += dy

            # enemy stun duration timer
            if self.enemy_stun_timer > 0:
                self.enemy_stun_timer -= 1

            # this updates the enemy position
            self.update_enemy()

            # the health and iframe Cooldown setup
            # iframe timer every frame tick
            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1

            # this Checks enemy collision to trigger question mode if not currently in iframes or active question
            if (
                self.check_enemy_hit()
                and self.hit_cooldown == 0
                and not self.in_question_mode
                and self.enemy_stun_timer == 0
            ):
                self.in_question_mode = True
                self.question_timer = 300  # 5 Seconds at 60 FPS (300 ticks)
                self.typewriter_index = 0  # the reset text animation index

            # the question timer and typewriter text update logic while in question mode
            if self.in_question_mode:
                # this increments the text typewriter character counter, 1 character added every 2 frames
                if self.typewriter_index < len(self.dialogue_full_text):
                    self.typewriter_index += 0.5

                # the 5 second timer
                self.question_timer -= 1
                if self.question_timer <= 0:
                    # if the Player takes longer than 5 seconds, deal a full heart
                    self.player_health -= 1.0
                    self.in_question_mode = False
                    self.hit_cooldown = self.max_hit_cooldown


            # Render the Frame
            self.screen.fill((240, 240, 240))  # Background
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

            # this Draws the enemy as yellow if currently stunned if not jus regular blue
            enemy_color = (255, 215, 0) if self.enemy_stun_timer > 0 else (5, 0, 139)     
            pygame.draw.rect(self.screen, enemy_color, enemy_rect) 

            # this Displays STUNNED! text marker above enemy when the enemy is in a 3 second stun state
            if self.enemy_stun_timer > 0:
                stun_surface = self.font.render("STUNNED!", True, (255, 140, 0))
                stun_rect = stun_surface.get_rect(center=(ex1 + half_e, ey1 - 15))
                self.screen.blit(stun_surface, stun_rect)


            # this displays "HIT!
            if self.check_enemy_hit():
                text_surface = self.font.render("HIT!", True, (255, 0, 0))
                text_rect = text_surface.get_rect(
                    center=(center_x, center_y - 30)
                )
                self.screen.blit(text_surface, text_rect)

            self.drawing_ofplayer_health()

            #  this Renders the Dialogue box when question state is triggered
            if self.in_question_mode:
                self.draw_retro_dialogue_box()

            pygame.display.flip()
            self.clock.tick(60)  # Lock to 60 FPS

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App()
