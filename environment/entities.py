import random

class Entity:
    def __init__(self, row, col):
        # tile coords
        self.row = row
        self.col = col

        self.tx = col
        self.ty = row

        # pixel coords (set later)
        self.x = 0
        self.y = 0

    def set_tile(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.col = tx
        self.row = ty

    def set_pixel_pos(self, px, py):
        self.x = px
        self.y = py

    def move(self, dr, dc, maze):
        new_r = self.row + dr
        new_c = self.col + dc

        if maze.in_bounds(new_r, new_c) and not maze.is_wall(new_r, new_c):
            self.set_tile(new_c, new_r)
            return True
        
        return False

class Pacman(Entity):
    def __init__(self, row, col):
        super().__init__(row, col)

        # Movement intent (dx, dy)
        self.intent = (0, 0)

        # Actual direction Pacman moves
        self.direction = (0, 0)

        # autopilot toggle
        self.autopilot = True

        # game stats
        self.score = 0
        
        # speed control
        self.normal_move_delay = 0.25      # your current pacman speed
        self.boost_move_delay = 0.20     # slightly faster only when chasing vuln ghosts
        self.move_delay = self.normal_move_delay

        self.time_since_move = 0

        # mouth animation
        self.mouth_open = True
        self.animation_timer = 0
        self.animation_speed = 0.12

        self.prev_tx=0
        self.prev_ty=0

    def set_intent(self, dx, dy):
        self.intent = (dx, dy)
        self.direction = (dx, dy)

    def toggle_autopilot(self):
        self.autopilot = not self.autopilot


class Ghost(Entity):
    def __init__(self, row, col):
        super().__init__(row, col)

        # ghost behavior state
        self.state = "normal"
        self.normal_move_delay = 0.30  # normal speed
        self.vulnerable_move_delay = 1.00  # slower when vulnerable
        self.move_delay = self.normal_move_delay        
        self.time_since_move = 0
        self.vulnerable_timer = 0.0

        self.prev_tx=0
        self.prev_ty=0

    def choose_move(self, maze, pacman_pos):

        # All possible 4 directions
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]

        # Randomize order
        random.shuffle(dirs)

        # Find ALL valid moves
        valid_moves = []
        for dx, dy in dirs:
            nx = self.tx + dx
            ny = self.ty + dy
            if not maze.is_wall(nx, ny):
                valid_moves.append((dx, dy))

        # If no moves (should never happen), do nothing
        if not valid_moves:
            return (0, 0)

        # --- NEW TRICK: DON’T ALLOW immediate 180° reversal ---
        # But WITHOUT storing memory in the ghost object
        # → We infer the previous move from position difference
        # → Simple, cheap, no state saved

        # Last move = current position - last “tile position”
        # This works because game_engine moves ghosts only by 1 tile each step
        last_dx = getattr(self, "_last_dx", 0)
        last_dy = getattr(self, "_last_dy", 0)

        reverse = (-last_dx, -last_dy)

        # Filter out reverse IF there is any alternative
        if reverse in valid_moves and len(valid_moves) > 1:
            valid_moves.remove(reverse)
        
        # --- RUN AWAY from Pacman if vulnerable ---
        if self.state == "vulnerable":
            # Calculate distance from each valid move to Pacman
            px, py = pacman_pos
            move_distances = []
            for dx, dy in valid_moves:
                nx, ny = self.tx + dx, self.ty + dy
                dist = abs(nx - px) + abs(ny - py)  # Manhattan distance
                move_distances.append(((dx, dy), dist))
            
            # Choose move that MAXIMIZES distance from Pacman
            move_distances.sort(key=lambda x: x[1], reverse=True)
            best_moves = [m for m in move_distances if m[1] == move_distances[0][1]]
            dx, dy = random.choice(best_moves)[0]
            
            # Save last move for next frame
            self._last_dx = dx
            self._last_dy = dy
            return dx, dy
        
        # Choose random valid move
        dx, dy = random.choice(valid_moves)

        # Save last move ONLY for next *frame's filtering*
        # (not long-term memory, just needed for 180° block)
        self._last_dx = dx
        self._last_dy = dy

        return dx, dy
