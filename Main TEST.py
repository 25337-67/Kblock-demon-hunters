import csv
import sys
import pygame

TILE_SIZE = 40  # Size of each grid square in pixels
COLOR_MAP = {  # RGB
    "0": (255, 255, 255),  # White (Wall)
    "1": (80, 80, 80),  # Dark Gray (Wall)
    "2": (100, 150, 220),  # Blue Tile  (Window)
    "3": (40, 40, 40),  # Black Tile (Door)
    "4": (240, 180, 130),  # Orange Tile (Wall)
    "5": (140, 140, 140),  # Light Gray (Floor)
    "6": (200, 200, 200),  # Lightish Gray (Outside Floor)
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

SOLID_TILES = {"0", "1", "2", "3", "4"}  # Walls
PORTAL_TILES = {
    "48",
    "49",
    "50",
    "51",
    "52",
    "53",
    "54",
    "55",
    "56",
    "57",
    "58",
    "59",
    "60",
    "61",
    "62",
    "63",
    "64",
    "65",
    "66",
    "67",
    "68",
    "69",
}


class App:

    def __init__(self):
        # Boot up Pygame
        pygame.init()  # initialise pygame
        self.screen = pygame.display.set_mode(
            (0, 0), pygame.FULLSCREEN
        )  # Open in fullscreen
        pygame.display.set_caption(
            "Northcote K-block demon hunters"
        )  # Window title
        self.clock = pygame.time.Clock()  # For capping FPS later

        # Track active map & defeated rooms (Updated to Level 3 (7))
        self.current_map_file = "MAP - Level 3 (8).csv"
        self.defeated_rooms = set()  # Remembers cleared classroom files
        self.locked_message_timer = 0  # Flash warning timer for locked doors

        # Player specs
        self.speed = 5
        self.player_size = 20

        # Player health setup
        self.max_health = 3  # max health capacity
        self.player_health = 3
        self.hit_cooldown = 0
        self.max_hit_cooldown = 60

        # Load CSV map and set spawns
        self.tile_map = []
        self.load_map(self.current_map_file)

        # Enemy specs & setup
        self.enemy_size = 20
        self.enemy_speed = 5
        self.enemy_max_health = 100
        self.enemy_health = 100
        self.enemy_active = False

        self.set_spawns_from_map()

        # Player attack setup
        self.attack_range = 30
        self.attack_damage = 5

        # Stun & Knockback setup
        self.max_stun_hits = 3
        self.enemy_stun_hits = 0
        self.enemy_knockback = 150
        self.knockback_duration = 15
        self.knockback_frames = 0
        self.knockback_step_x = 0
        self.knockback_step_y = 0
        self.enemy_stun_timer = 0

        # Dialogue state tracking
        self.in_question_mode = False
        self.question_timer = 0
        self.typewriter_index = 0
        self.dialogue_full_text = "yo g, Are apples red?"

        # Fonts
        self.font = pygame.font.SysFont("Courier New", 22, bold=True)
        self.subfont = pygame.font.SysFont("Courier New", 18, bold=True)

        # Heart sprites
        self.img_full = pygame.image.load("full_heart.png").convert_alpha()
        self.img_half = pygame.image.load("half_heart.png").convert_alpha()
        self.img_empty = pygame.image.load("empty_heart.png").convert_alpha()

        heart_size = (24, 24)
        self.img_full = pygame.transform.scale(self.img_full, heart_size)
        self.img_half = pygame.transform.scale(self.img_half, heart_size)
        self.img_empty = pygame.transform.scale(self.img_empty, heart_size)

        self.run_game()

    def load_map(self, filename):
        """Loads CSV map data safely with fallback error handling."""
        self.tile_map = []
        try:
            with open(filename, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    map_row = []
                    for col in row:
                        val = col.strip()
                        if val and val.lower() != "nan":
                            try:
                                val = str(int(float(val)))
                            except ValueError:
                                val = val.upper()
                        else:
                            val = None
                        map_row.append(val)
                    self.tile_map.append(map_row)
        except FileNotFoundError:
            print(f"Error: {filename} not found.")

    def set_spawns_from_map(self):
        """Finds 'P' (Player) and 'E' (Enemy) spawn markers in current CSV."""
        player_col, player_row = 7, 0
        has_enemy_spawn = False
        enemy_col, enemy_row = 0, 0

        for r_idx, row in enumerate(self.tile_map):
            for c_idx, tile in enumerate(row):
                if tile == "P":
                    player_col, player_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = "5"
                elif tile == "E":
                    has_enemy_spawn = True
                    enemy_col, enemy_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = "5"

        self.player_x = player_col * TILE_SIZE + (TILE_SIZE // 2)
        self.player_y = player_row * TILE_SIZE + (TILE_SIZE // 2)

        if has_enemy_spawn and self.current_map_file not in self.defeated_rooms:
            self.enemy_active = True
            self.enemy_health = self.enemy_max_health
            self.enemy_x = enemy_col * TILE_SIZE + (TILE_SIZE // 2)
            self.enemy_y = enemy_row * TILE_SIZE + (TILE_SIZE // 2)
        else:
            self.enemy_active = False

    def change_room(self, target_map_file, spawn_col, spawn_row):
        """Swaps active CSV map, spawns player at door position, and handles room enemy spawning."""
        self.current_map_file = target_map_file
        self.load_map(target_map_file)

        self.player_x = spawn_col * TILE_SIZE + (TILE_SIZE // 2)
        self.player_y = spawn_row * TILE_SIZE + (TILE_SIZE // 2)

        has_enemy_spawn = False
        enemy_col, enemy_row = 0, 0
        for r_idx, row in enumerate(self.tile_map):
            for c_idx, tile in enumerate(row):
                if tile == "E":
                    has_enemy_spawn = True
                    enemy_col, enemy_row = c_idx, r_idx
                    self.tile_map[r_idx][c_idx] = "5"

        if has_enemy_spawn and self.current_map_file not in self.defeated_rooms:
            self.enemy_active = True
            self.enemy_health = self.enemy_max_health
            self.enemy_x = enemy_col * TILE_SIZE + (TILE_SIZE // 2)
            self.enemy_y = enemy_row * TILE_SIZE + (TILE_SIZE // 2)
        else:
            self.enemy_active = False

    def get_camera_pos(self, screen_w, screen_h):
        if not self.tile_map or not self.tile_map[0]:
            return 0, 0

        p_row = max(
            0, min(int(self.player_y // TILE_SIZE), len(self.tile_map) - 1)
        )
        p_col = max(
            0, min(int(self.player_x // TILE_SIZE), len(self.tile_map[0]) - 1)
        )

        left_c = p_col
        while left_c > 0 and self.tile_map[p_row][left_c - 1] is not None:
            left_c -= 1
        right_c = p_col
        while (
            right_c < len(self.tile_map[0]) - 1
            and self.tile_map[p_row][right_c + 1] is not None
        ):
            right_c += 1

        top_r = p_row
        while top_r > 0 and self.tile_map[top_r - 1][p_col] is not None:
            top_r -= 1
        bottom_r = p_row
        while (
            bottom_r < len(self.tile_map) - 1
            and self.tile_map[bottom_r + 1][p_col] is not None
        ):
            bottom_r += 1

        min_x = left_c * TILE_SIZE
        max_x = (right_c + 1) * TILE_SIZE
        min_y = top_r * TILE_SIZE
        max_y = (bottom_r + 1) * TILE_SIZE

        if max_x - min_x <= screen_w:
            cam_x = min_x - (screen_w - (max_x - min_x)) / 2
        else:
            cam_x = max(
                min_x, min(self.player_x - screen_w / 2, max_x - screen_w)
            )

        if max_y - min_y <= screen_h:
            cam_y = min_y - (screen_h - (max_y - min_y)) / 2
        else:
            cam_y = max(
                min_y, min(self.player_y - screen_h / 2, max_y - screen_h)
            )

        return cam_x, cam_y

    def check_collision(self, next_x, next_y, object_size=20):
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
                if (
                    r < 0
                    or r >= len(self.tile_map)
                    or c < 0
                    or c >= len(self.tile_map[0])
                ):
                    return True

                val = self.tile_map[r][c]
                if val is None or val in SOLID_TILES:
                    return True
        return False

    def check_enemy_wall_collision(self, next_x, next_y):
        return self.check_collision(next_x, next_y, self.enemy_size)

    def update_enemy(self):
        if (
            not self.enemy_active
            or self.in_question_mode
            or self.enemy_stun_timer > 0
            or self.knockback_frames > 0
        ):
            return
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
        if not self.enemy_active:
            return False

        half_p = self.player_size / 2
        half_e = self.enemy_size / 2

        p_left, p_right = self.player_x - half_p, self.player_x + half_p
        p_top, p_bottom = self.player_y - half_p, self.player_y + half_p

        e_left, e_right = self.enemy_x - half_e, self.enemy_x + half_e
        e_top, e_bottom = self.enemy_y - half_e, self.enemy_y + half_e

        if not (
            p_right <= e_left
            or p_left >= e_right
            or p_bottom <= e_top
            or p_top >= e_bottom
        ):
            return True
        return False

    def check_enemy_attack_range(self):
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        distance = (dx**2 + dy**2) ** 0.5
        return distance <= self.attack_range

    def knockback_enemy(self):
        dx = self.enemy_x - self.player_x
        dy = self.enemy_y - self.player_y
        distance = (dx**2 + dy**2) ** 0.5

        if distance == 0:
            dx = 1
            dy = 0
            distance = 1

        direction_x = dx / distance
        direction_y = dy / distance

        self.knockback_step_x = direction_x * (
            self.enemy_knockback / self.knockback_duration
        )
        self.knockback_step_y = direction_y * (
            self.enemy_knockback / self.knockback_duration
        )
        self.knockback_frames = self.knockback_duration

    def update_enemy_knockback(self):
        if self.knockback_frames <= 0:
            return

        steps = max(
            1, int(max(abs(self.knockback_step_x), abs(self.knockback_step_y))) + 1
        )
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
        start_x, start_y, spacing = 25, 25, 35

        for i in range(self.max_health):
            container_hp = self.player_health - i

            if container_hp >= 1.0:
                sprite = self.img_full
            elif container_hp == 0.5:
                sprite = self.img_half
            else:
                sprite = self.img_empty

            current_x = start_x + (i * spacing)
            self.screen.blit(sprite, (current_x, start_y))

    def drawing_ofenemy_health(self):
        if not self.enemy_active:
            return

        screen_w, screen_h = self.screen.get_size()
        bar_width = 400
        bar_height = 20
        bar_x = (screen_w - bar_width) // 2
        bar_y = 25

        health_ratio = self.enemy_health / self.enemy_max_health
        current_bar_width = bar_width * health_ratio

        pygame.draw.rect(
            self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.screen,
            (200, 40, 40),
            (bar_x, bar_y, current_bar_width, bar_height),
        )
        pygame.draw.rect(
            self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2
        )

    def draw_dialogue_box(self):
        screen_w, screen_h = self.screen.get_size()
        box_w, box_h = 600, 160
        box_x = (screen_w - box_w) // 2
        box_y = screen_h - box_h - 40

        pygame.draw.rect(self.screen, (0, 0, 0), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(
            self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), 5
        )

        visible_text = self.dialogue_full_text[: int(self.typewriter_index)]
        text_surface = self.font.render(visible_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (box_x + 25, box_y + 25))

        if self.typewriter_index >= len(self.dialogue_full_text):
            options_surface = self.subfont.render(
                "[O] YES          [X] NO", True, (255, 255, 255)
            )
            self.screen.blit(options_surface, (box_x + 25, box_y + 75))

        time_left_sec = max(0.0, self.question_timer / 60.0)
        timer_surface = self.subfont.render(
            f"TIME: {time_left_sec:.1f}s", True, (255, 255, 0)
        )
        self.screen.blit(
            timer_surface, (box_x + box_w - 150, box_y + box_h - 35)
        )

    def run_game(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

                if self.in_question_mode and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y or event.key == pygame.K_o:
                        self.in_question_mode = False
                        self.enemy_stun_timer = 180
                        self.enemy_stun_hits = 0
                        self.hit_cooldown = self.max_hit_cooldown
                    elif event.key == pygame.K_n or event.key == pygame.K_x:
                        self.player_health -= 0.5
                        self.in_question_mode = False
                        self.hit_cooldown = self.max_hit_cooldown

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if (
                        self.enemy_active
                        and self.enemy_stun_timer > 0
                        and self.knockback_frames == 0
                        and self.check_enemy_attack_range()
                        and self.enemy_stun_hits < self.max_stun_hits
                    ):
                        self.enemy_health = max(
                            0, self.enemy_health - self.attack_damage
                        )
                        self.enemy_stun_hits += 1
                        self.knockback_enemy()

                        if self.enemy_health <= 0:
                            self.enemy_active = False
                            self.defeated_rooms.add(self.current_map_file)

                        if self.enemy_stun_hits >= self.max_stun_hits:
                            self.enemy_stun_timer = 0

            if not self.in_question_mode:
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

                # --- DYNAMIC DOOR TRANSITIONS & LOCK CHECK ---
                current_col = int(self.player_x // TILE_SIZE)
                current_row = int(self.player_y // TILE_SIZE)

                if 0 <= current_row < len(self.tile_map) and 0 <= current_col < len(
                    self.tile_map[0]
                ):
                    tile_val = self.tile_map[current_row][current_col]

                    if tile_val in PORTAL_TILES:
                        if (
                            self.current_map_file != "MAP - Level 3 (8).csv"
                            and self.enemy_active
                        ):
                            self.locked_message_timer = 90
                            self.player_y -= TILE_SIZE // 2
                        else:
                            if tile_val == "48":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science 1 Classroom 48_49.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=9,
                                        spawn_row=13,
                                    )

                            elif tile_val == "49":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science 1 Classroom 48_49.csv",
                                        spawn_col=31,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=15,
                                        spawn_row=13,
                                    )

                            elif tile_val == "50":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Math classroom Test 50_51.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=18,
                                        spawn_row=13,
                                    )

                            elif tile_val == "51":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Math classroom Test 50_51.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=24,
                                        spawn_row=13,
                                    )

                            elif tile_val == "52":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 52_53.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=27,
                                        spawn_row=13,
                                    )

                            elif tile_val == "53":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 52_53.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=33,
                                        spawn_row=13,
                                    )

                            elif tile_val == "54":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 54_55.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=36,
                                        spawn_row=13,
                                    )

                            elif tile_val == "55":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - 54_55.csv",
                                        spawn_col=34,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=42,
                                        spawn_row=13,
                                    )

                            elif tile_val == "56":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 56_57.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=16,
                                        spawn_row=22,
                                    )

                            elif tile_val == "57":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 56_57.csv",
                                        spawn_col=29,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=23,
                                        spawn_row=22,
                                    )

                            elif tile_val == "58":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 58_59.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=27,
                                        spawn_row=22,
                                    )

                            elif tile_val == "59":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 58_59.csv",
                                        spawn_col=29,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=33,
                                        spawn_row=22,
                                    )

                            elif tile_val == "60":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 60_61.csv",
                                        spawn_col=4,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=37,
                                        spawn_row=22,
                                    )

                            elif tile_val == "61":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Science Classroom 60_61.csv",
                                        spawn_col=29,
                                        spawn_row=20,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=45,
                                        spawn_row=22,
                                    )

                            elif tile_val == "62":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 62_63 (4).csv",
                                        spawn_col=6,
                                        spawn_row=8,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=70,
                                        spawn_row=28,
                                    )

                            elif tile_val == "63":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 62_63 (4).csv",
                                        spawn_col=18,
                                        spawn_row=22,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=82,
                                        spawn_row=44,
                                    )

                            elif tile_val == "64":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Copy of Food room 62_63 (1).csv",
                                        spawn_col=15,
                                        spawn_row=27,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=89,
                                        spawn_row=40,
                                    )

                            elif tile_val == "65":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Copy of Food room 62_63 (1).csv",
                                        spawn_col=34,
                                        spawn_row=6,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=101,
                                        spawn_row=15,
                                    )

                            elif tile_val == "66":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 66_67.csv",
                                        spawn_col=14,
                                        spawn_row=4,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=81,
                                        spawn_row=61,
                                    )

                            elif tile_val == "67":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 66_67.csv",
                                        spawn_col=14,
                                        spawn_row=23,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=81,
                                        spawn_row=72,
                                    )

                            elif tile_val == "68":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 68_69 (1).csv",
                                        spawn_col=21,
                                        spawn_row=4,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=89,
                                        spawn_row=61,
                                    )

                            elif tile_val == "69":
                                if self.current_map_file == "Map - Level 3 (8).csv":
                                    self.change_room(
                                        "MAP - Food room 68_69 (1).csv",
                                        spawn_col=21,
                                        spawn_row=27,
                                    )
                                else:
                                    self.change_room(
                                        "Map - Level 3 (8).csv",
                                        spawn_col=89,
                                        spawn_row=77,
                                    )

            if self.enemy_stun_timer > 0:
                self.enemy_stun_timer -= 1

            self.update_enemy_knockback()
            self.update_enemy()

            if self.hit_cooldown > 0:
                self.hit_cooldown -= 1

            if (
                self.enemy_active
                and self.check_enemy_hit()
                and self.hit_cooldown == 0
                and not self.in_question_mode
                and self.enemy_stun_timer == 0
            ):
                self.in_question_mode = True
                self.question_timer = 300
                self.typewriter_index = 0

            if self.in_question_mode:
                if self.typewriter_index < len(self.dialogue_full_text):
                    self.typewriter_index += 0.5

                self.question_timer -= 1
                if self.question_timer <= 0:
                    self.player_health -= 1.0
                    self.in_question_mode = False
                    self.hit_cooldown = self.max_hit_cooldown

            # Render Frame
            self.screen.fill((240, 240, 240))
            screen_w, screen_h = self.screen.get_size()

            cam_x, cam_y = self.get_camera_pos(screen_w, screen_h)

            for r_idx, row in enumerate(self.tile_map):
                for c_idx, tile_id in enumerate(row):
                    if tile_id is not None and tile_id in COLOR_MAP:
                        world_x = c_idx * TILE_SIZE
                        world_y = r_idx * TILE_SIZE
                        screen_x = world_x - cam_x
                        screen_y = world_y - cam_y

                        if (
                            -TILE_SIZE <= screen_x <= screen_w
                            and -TILE_SIZE <= screen_y <= screen_h
                        ):
                            tile_rect = pygame.Rect(
                                screen_x, screen_y, TILE_SIZE, TILE_SIZE
                            )
                            pygame.draw.rect(
                                self.screen, COLOR_MAP[tile_id], tile_rect
                            )

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

            # Draw enemy
            if self.enemy_active:
                half_e = self.enemy_size / 2
                ex1 = (self.enemy_x - cam_x) - half_e
                ey1 = (self.enemy_y - cam_y) - half_e
                enemy_rect = pygame.Rect(
                    ex1, ey1, self.enemy_size, self.enemy_size
                )

                enemy_color = (
                    (255, 215, 0) if self.enemy_stun_timer > 0 else (5, 0, 139)
                )
                pygame.draw.rect(self.screen, enemy_color, enemy_rect)

                if self.enemy_stun_timer > 0:
                    stun_surface = self.font.render(
                        "STUNNED!", True, (255, 140, 0)
                    )
                    stun_rect = stun_surface.get_rect(
                        center=(ex1 + half_e, ey1 - 15)
                    )
                    self.screen.blit(stun_surface, stun_rect)

                if self.check_enemy_hit():
                    text_surface = self.font.render("HIT!", True, (255, 0, 0))
                    text_rect = text_surface.get_rect(
                        center=(player_screen_x, player_screen_y - 30)
                    )
                    self.screen.blit(text_surface, text_rect)

            self.drawing_ofplayer_health()
            self.drawing_ofenemy_health()

            # Render "DOOR IS LOCKED" message overlay
            if self.locked_message_timer > 0:
                self.locked_message_timer -= 1
                msg_surface = self.font.render(
                    "DOOR IS LOCKED! DEFEAT THE DEMON FIRST!", True, (255, 0, 0)
                )
                msg_rect = msg_surface.get_rect(
                    center=(screen_w // 2, screen_h // 2 - 100)
                )
                pygame.draw.rect(
                    self.screen, (0, 0, 0), msg_rect.inflate(20, 10)
                )
                pygame.draw.rect(
                    self.screen, (255, 0, 0), msg_rect.inflate(20, 10), 2
                )
                self.screen.blit(msg_surface, msg_rect)

            if self.in_question_mode:
                self.draw_dialogue_box()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App()
