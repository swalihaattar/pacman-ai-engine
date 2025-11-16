import os
import random
import math

from .maze import Maze, PELLET, POWER, PACMAN, GHOST, WALL, DEFAULT_MAP
from .entities import Pacman, Ghost
from ai_modules.controller import HybridController


TILE_SIZE = 28
HIGHSCORE_FILE = "highscore.txt"


# ----------------------------------------------------------
# Persistent Highscore
# ----------------------------------------------------------
def load_highscore():
    if not os.path.exists(HIGHSCORE_FILE):
        return 0
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass



class GameEngine:

    # ----------------------------------------------------------
    def __init__(self, map_lines=None):
        # Persistent highscore
        self.highscore = load_highscore()

        # Load map
        if map_lines is None:
            map_lines = DEFAULT_MAP

        self.original_map = [row[:] for row in map_lines]
        self.maze = Maze(map_lines)

        self.tile_size = TILE_SIZE
        self.width_px = self.maze.width * TILE_SIZE
        self.height_px = self.maze.height * TILE_SIZE

        # Game objects
        self.pellets = set()
        self.power_pellets = set()
        self.pacman = None
        self.ghosts = []

        self._load_from_map()

        # AI controller
        self.controller = HybridController()

        # Game state
        self.running = True
        self.game_over = False
        self.win = False
        self.step_time = 0



    # ----------------------------------------------------------
    def _load_from_map(self):
        for y, row in enumerate(self.maze.raw):
            for x, ch in enumerate(row):

                if ch == '.':
                    self.pellets.add((x, y))
                    self.maze.raw[y][x] = ' '

                elif ch == 'o':
                    self.power_pellets.add((x, y))
                    self.maze.raw[y][x] = ' '

                elif ch == 'P':
                    self.pacman = Pacman(y, x)
                    self.maze.raw[y][x] = ' '

                elif ch == 'G':
                    self.ghosts.append(Ghost(y, x))
                    self.maze.raw[y][x] = ' '


        # Default pacman location
        if self.pacman is None:
            cx = self.maze.width // 2   # x (col)
            cy = self.maze.height // 2  # y (row)
            self.pacman = Pacman(cy, cx)  # pass (row, col)


        # Pixel positions
        px, py = self.maze.tile_center(self.pacman.tx, self.pacman.ty, self.tile_size)
        self.pacman.set_pixel_pos(px, py)

        for g in self.ghosts:
            gx, gy = self.maze.tile_center(g.tx, g.ty, self.tile_size)
            g.set_pixel_pos(gx, gy)



    # ----------------------------------------------------------
    # Reset game without touching highscore
    # ----------------------------------------------------------
    def reset(self):
        self.maze = Maze(self.original_map)

        self.pellets = set()
        self.power_pellets = set()
        self.ghosts = []
        self.pacman = None

        self._load_from_map()

        self.running = True
        self.game_over = False
        self.win = False
        self.step_time = 0



    # ----------------------------------------------------------
    def handle_keydown(self, key):
        import pygame

        if key == pygame.K_UP: self.pacman.set_intent(0,-1)
        elif key == pygame.K_DOWN: self.pacman.set_intent(0,1)
        elif key == pygame.K_LEFT: self.pacman.set_intent(-1,0)
        elif key == pygame.K_RIGHT: self.pacman.set_intent(1,0)
        elif key == pygame.K_a: self.pacman.toggle_autopilot()
        elif key == pygame.K_SPACE: self.reset()



    # ----------------------------------------------------------
    def update(self, dt):
        if self.game_over:
            return

        self.step_time += dt

        # ------------------------------------------------------
        # WIN condition → save highscore
        # ------------------------------------------------------
        if not self.pellets and not self.power_pellets:
            self.win = True
            self.running = False
            self.game_over = True

            if self.pacman.score > self.highscore:
                self.highscore = self.pacman.score
                save_highscore(self.highscore)

            return


        # ----------------- AUTOPILOT AI -----------------------
        if self.pacman.autopilot:
            escape = self._runaway_from_threat()

            if escape:
                self.pacman.set_intent(*escape)
            else:
                chase = self._nearest_vulnerable_ghost_direction()

                if chase:
                    self.pacman.set_intent(*chase)
                else:
                    dx, dy = self.controller.choose_action(self)

                    # fallback if AI stuck
                    if (dx, dy) == (0,0) or self.maze.is_wall(self.pacman.tx+dx, self.pacman.ty+dy):
                        dx, dy = self._greedy_step_to_nearest_pellet()

                    self.pacman.set_intent(dx, dy)


        # ------------------------------------------------------
        # PACMAN MOVEMENT
        # ------------------------------------------------------
        self.pacman.time_since_move += dt

        if self.pacman.time_since_move >= self.pacman.move_delay:
            self.pacman.time_since_move = 0

            dx, dy = self.pacman.direction

            nx = self.pacman.tx + dx
            ny = self.pacman.ty + dy

            if not self.maze.is_wall(nx, ny):
                self.pacman.set_tile(nx, ny)
                px, py = self.maze.tile_center(nx, ny, self.tile_size)
                self.pacman.set_pixel_pos(px, py)

                self.pacman.animation_timer += dt
                if self.pacman.animation_timer >= self.pacman.animation_speed:
                    self.pacman.animation_timer = 0
                    self.pacman.mouth_open = not self.pacman.mouth_open



        # ------------------------------------------------------
        # PELLET CONSUMPTION
        # ------------------------------------------------------
        pos = (self.pacman.tx, self.pacman.ty)

        if pos in self.pellets:
            self.pellets.remove(pos)
            self.pacman.score += 10

        if pos in self.power_pellets:
            self.power_pellets.remove(pos)
            self.pacman.score += 25
            self.pacman.move_delay = self.pacman.boost_move_delay

            for g in self.ghosts:
                g.state = "vulnerable"
                g.vulnerable_timer = 5



        # ------------------------------------------------------
        # GHOST MOVEMENT
        # ------------------------------------------------------
        for g in self.ghosts:
            g.prev_tx, g.prev_ty = g.tx, g.ty

            g.time_since_move += dt

            if g.state == "vulnerable":
                g.vulnerable_timer -= dt
                if g.vulnerable_timer <= 0:
                    g.state = "normal"

                if all(gg.state == "normal" for gg in self.ghosts):
                    self.pacman.move_delay = self.pacman.normal_move_delay

            if g.time_since_move < g.move_delay:
                continue

            g.time_since_move = 0

            dxg, dyg = g.choose_move(self.maze, pos)

            ngx, ngy = g.tx + dxg, g.ty + dyg
            if not self.maze.is_wall(ngx, ngy):
                g.set_tile(ngx, ngy)
                gx, gy = self.maze.tile_center(ngx, ngy, self.tile_size)
                g.set_pixel_pos(gx, gy)



        # ------------------------------------------------------
        # COLLISION CHECK
        # ------------------------------------------------------
        for g in self.ghosts:

            # direct collision
            if (g.tx, g.ty) == (self.pacman.tx, self.pacman.ty):
                self._handle_ghost_collision(g)

            # swap collision
            if (g.prev_tx, g.prev_ty) == (self.pacman.tx, self.pacman.ty) and \
               (self.pacman.prev_tx, self.pacman.prev_ty) == (g.tx, g.ty):
                self._handle_ghost_collision(g)



    # ----------------------------------------------------------
    def _handle_ghost_collision(self, g):

        # Pac-Man eats ghost
        if g.state == "vulnerable":
            self.pacman.score += 50

            g.set_tile(1, 1)
            g.set_pixel_pos(*self.maze.tile_center(1, 1, self.tile_size))
            g.state = "normal"
            g.vulnerable_timer = 0
            return

        # --------------------
        # PACMAN DIES
        # --------------------
        self.running = False
        self.game_over = True
        self.win = False

        # Save new highscore
        if self.pacman.score > self.highscore:
            self.highscore = self.pacman.score
            save_highscore(self.highscore)



    # ----------------------------------------------------------
    def get_state_snapshot(self):
        return {
            "width": self.maze.width,
            "height": self.maze.height,
            "tile_size": self.tile_size,
            "pacman": self.pacman,
            "ghosts": self.ghosts,
            "pellets": self.pellets,
            "power_pellets": self.power_pellets,
            "maze": self.maze
        }



    # ----------------------------------------------------------
    # AI HELPERS
    # ----------------------------------------------------------
    def _runaway_from_threat(self, danger_radius=2):
        threats = [(g.tx, g.ty) for g in self.ghosts if g.state == "normal"]
        if not threats:
            return None

        px, py = self.pacman.tx, self.pacman.ty

        close = [(gx, gy) for gx, gy in threats
                 if abs(gx - px) + abs(gy - py) <= danger_radius]

        if not close:
            return None

        best_dirs = []
        best_dist = -1

        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = px + dx, py + dy
            if self.maze.is_wall(nx, ny):
                continue

            min_d = min(abs(gx - nx) + abs(gy - ny) for gx, gy in close)

            if min_d > best_dist:
                best_dist = min_d
                best_dirs = [(dx, dy)]
            elif min_d == best_dist:
                best_dirs.append((dx, dy))

        return random.choice(best_dirs) if best_dirs else None



    def _nearest_vulnerable_ghost_direction(self):
        vuln = [(g.tx, g.ty) for g in self.ghosts if g.state == "vulnerable"]
        if not vuln:
            return None

        dist = self.maze.bfs_distance_grid(vuln)
        start = (self.pacman.tx, self.pacman.ty)

        if start not in dist:
            return None

        curr = dist[start]

        best = []
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = start[0]+dx, start[1]+dy
            if not self.maze.is_wall(nx, ny) and (nx, ny) in dist:
                if dist[(nx, ny)] < curr:
                    best.append((dx, dy))

        return random.choice(best) if best else None



    def _greedy_step_to_nearest_pellet(self):
        targets = list(self.pellets | self.power_pellets)
        if not targets:
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = self.pacman.tx + dx, self.pacman.ty + dy
                if not self.maze.is_wall(nx, ny):
                    return (dx, dy)
            return (0, 0)

        dist = self.maze.bfs_distance_grid(targets)
        start = (self.pacman.tx, self.pacman.ty)

        if start not in dist:
            return (0,0)

        curr = dist[start]
        candidates = []

        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = start[0]+dx, start[1]+dy
            if self.maze.is_wall(nx, ny): continue
            if (nx, ny) in dist:
                candidates.append(((dx, dy), dist[(nx, ny)], (nx, ny)))

        if not candidates:
            return (0,0)

        better = [c for c in candidates if c[1] < curr]
        pick = better if better else candidates

        safe = [c for c in pick if not self._is_tile_dangerous(c[2][0], c[2][1])]
        if safe:
            pick = safe

        pick.sort(key=lambda x: x[1])
        best = [c for c in pick if c[1] == pick[0][1]]

        return random.choice(best)[0]


    def _is_tile_dangerous(self, tx, ty, danger_radius=2):
        for g in self.ghosts:
            if g.state == "normal":
                if abs(g.tx - tx) + abs(g.ty - ty) <= danger_radius:
                    return True
        return False
