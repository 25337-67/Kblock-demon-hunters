import tkinter as tk


class App:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Northcote K-block demon hunters")
        self.root.attributes("-fullscreen", True)

        self.main_canvas = tk.Canvas(self.root, background="#F0F0F0")
        self.main_canvas.pack(fill="both", expand=True)

        self.speed = 5
        self.player_size = 20

        # World Position of the player
        self.player_x = 0
        self.player_y = 0

        # da enemy setup
        self.enemy_size = 20
        self.enemy_speed = 5
        self.enemy_x = 300  #makes it so dat it starts away from da player  
        self.enemy_y = 200

        # Define Wall obstacles in World Coordinates: (x1, y1, x2, y2)
        self.walls_world = [
            (-100, -150, 100, -100),  # Top wall
            (150, -100, 200, 200),  # Right side pillar
            (-200, -150, -150, 150)
        ]

        # Draw Wall visuals on canvas
        self.wall_items = []
        for _ in self.walls_world:
            wall_id = self.main_canvas.create_rectangle(
                0, 0, 0, 0, fill="#FF6B6B", outline=""
            )
            self.wall_items.append(wall_id)

        # Draw Player Visual
        self.player_block = self.main_canvas.create_rectangle(
            0, 0, 0, 0, fill="#92EEFF", outline=""
        )

        # ts draws the enemy visual
        self.enemy_block = self.main_canvas.create_rectangle(
             0, 0, 0, 0, fill="#05008B", outline=""
        )

        #creates da text marker 
        self.hit_text = self.main_canvas.create_text(
            0, 0, text="", fill="red", font=("Arial", 24, "bold")
        )


        self.pressed_keys = set()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())  #exit

        self.game_loop()

    def on_key_press(self, event):
        self.pressed_keys.add(event.keysym.lower())

    def on_key_release(self, event):
        self.pressed_keys.discard(event.keysym.lower())

    def check_collision(self, next_x, next_y):
        """Checks if player bounding box at (next_x, next_y) intersects any wall."""
        half_size = self.player_size / 2
        p_left = next_x - half_size
        p_right = next_x + half_size
        p_top = next_y - half_size
        p_bottom = next_y + half_size

        for wx1, wy1, wx2, wy2 in self.walls_world:
            if not (
                p_right <= wx1
                or p_left >= wx2
                or p_bottom <= wy1
                or p_top >= wy2
            ):
                return True
        return False





    
    def update_enemy(self):
        #ts moves the enemy towards da players main positions
        dx = self.player_x - self.enemy_x
        dy = self.player_y - self.enemy_y
        dist = (dx**2 + dy**2) ** 0.5

        if dist != 0:
            #moves along da vector pointing towards da player   
            self.enemy_x += (dx / dist) * self.enemy_speed
            self.enemy_y += (dy / dist) * self.enemy_speed




    def check_enemy_hit(self):
        #dis check da box collision between player and enemy
        half_p = self.player_size / 2
        half_e = self.enemy_size / 2

        p_left, p_right = self.player_x - half_p, self.player_x + half_p
        p_top, p_bottom = self.player_y - half_p, self.player_y + half_p

        e_left, e_right = self.enemy_x - half_e, self.enemy_x + half_e
        e_top, e_bottom = self.enemy_y - half_e, self.enemy_y + half_e

        #checks for overlaps
        if not (
            p_right <= e_left
            or p_left >= e_right
            or p_bottom <= e_top
            or p_top >= e_bottom
        ):
            return True
        return False



    def render_world(self):
        """Renders walls relative to the player, keeping the player strictly centered."""
        screen_w = self.main_canvas.winfo_width()
        screen_h = self.main_canvas.winfo_height()

        if screen_w <= 1:
            screen_w, screen_h = 600, 400

        center_x = screen_w / 2
        center_y = screen_h / 2

        # 1. Position Walls relative to player's world position
        for item_id, (wx1, wy1, wx2, wy2) in zip(
            self.wall_items, self.walls_world
        ):
            sx1 = wx1 - self.player_x + center_x
            sy1 = wy1 - self.player_y + center_y
            sx2 = wx2 - self.player_x + center_x
            sy2 = wy2 - self.player_y + center_y
            self.main_canvas.coords(item_id, sx1, sy1, sx2, sy2)

        # 2. Player stays permanently locked at screen center
        half_p = self.player_size / 2
        px1 = center_x - half_p
        py1 = center_y - half_p
        px2 = center_x + half_p
        py2 = center_y + half_p

        self.main_canvas.coords(self.player_block, px1, py1, px2, py2)



        #positions da enemy relative to da players position in da world
        half_e = self.enemy_size / 2
        ex1 = (self.enemy_x - self.player_x + center_x) - half_e
        ey1 = (self.enemy_y - self.player_y + center_y) - half_e
        ex2 = (self.enemy_x - self.player_x + center_x) + half_e
        ey2 = (self.enemy_y - self.player_y + center_y) + half_e




        self.main_canvas.coords(self.enemy_block, ex1, ey1, ex2, ey2)

        #dis would diaplay da word hit! on top of da player position when dey take dmg
        if self.check_enemy_hit():
                    self.main_canvas.coords(self.hit_text, center_x, center_y - 30)
                    self.main_canvas.itemconfig(self.hit_text, text="HIT!")
        else:
                    self.main_canvas.itemconfig(self.hit_text, text="")




    def game_loop(self):
        dx, dy = 0, 0

        if "up" in self.pressed_keys or "w" in self.pressed_keys:
            dy -= self.speed
        if "down" in self.pressed_keys or "s" in self.pressed_keys:
            dy += self.speed
        if "left" in self.pressed_keys or "a" in self.pressed_keys:
            dx -= self.speed
        if "right" in self.pressed_keys or "d" in self.pressed_keys:
            dx += self.speed

        # Move player horizontally if no collision
        if dx != 0 and not self.check_collision(self.player_x + dx, self.player_y):
            self.player_x += dx

        # Move player vertically if no collision
        if dy != 0 and not self.check_collision(self.player_x, self.player_y + dy):
            self.player_y += dy


        #updates da enemy position
        self.update_enemy()

        
        # Redraw scene with centered camera tracking
        self.render_world()

        self.root.after(16, self.game_loop)


if __name__ == "__main__":
    app = App()
    app.root.mainloop()
