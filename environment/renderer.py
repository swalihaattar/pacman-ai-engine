import pygame
from pygame import Rect
from .game_engine import TILE_SIZE
from .maze import WALL
import math

# color palette
BLACK = (0,0,0)
WHITE = (240,240,240)
WALL_COLOR = (30,30,120)
PELLET_COLOR = (200,180,0)
POWER_COLOR = (255,100,0)
PACMAN_COLOR = (255, 220, 0)
GHOST_COLOR = (200, 50, 50)
GRID_COLOR = (60,60,60)

FONT_SIZE = 18

class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.tile_size = engine.tile_size
        self.width = engine.width_px
        self.hud_height = 40
        self.height = engine.height_px + self.hud_height

        # font
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", FONT_SIZE)
        self.mouth_open = True
        self.last_mouth_toggle = 0
        self.mouth_interval = 150   # ms (controls animation speed)


    def render(self, screen):
        if not self.engine.running and self.engine.game_over:
            # Dynamically size Game Over screen (90% of current window)
            GAMEOVER_WIDTH = int(self.width * 0.9)
            GAMEOVER_HEIGHT = int(self.height * 0.9)
            
            # Create surface
            gameover_screen = pygame.Surface((GAMEOVER_WIDTH, GAMEOVER_HEIGHT))
            gameover_screen.fill(BLACK)
            
            # Base for scaling fonts
            base = min(GAMEOVER_WIDTH, GAMEOVER_HEIGHT)
            msg_font = pygame.font.SysFont("Arial", max(20, base // 16), bold=True)
            score_font = pygame.font.SysFont("Arial", max(16, base // 22))
            level_font = pygame.font.SysFont("Arial", max(14, base // 28))
            hint_font = pygame.font.SysFont("Arial", max(12, base // 38))

            # Check message
            if getattr(self.engine, 'all_levels_complete', False):
                msg = "ALL LEVELS COMPLETE!"
                msg_color = (255, 215, 0)
            else:
                msg = "LEVEL COMPLETE!" if self.engine.win else "GAME OVER"
                msg_color = (0, 255, 0) if self.engine.win else (255, 50, 50)

            # Render text
            surf = msg_font.render(msg, True, msg_color)
            level_display = self.engine.current_level_name.upper()
            level_surf = level_font.render(f"Level: {level_display}", True, (200, 200, 200))
            score_surf = score_font.render(f"Score: {self.engine.pacman.score}", True, WHITE)
            highscore_surf = level_font.render(f"High Score: {self.engine.get_current_highscore()}", True, (255, 215, 0))

            # Hint
            if self.engine.win and not getattr(self.engine, 'all_levels_complete', False):
                hint_surf = hint_font.render("Press ENTER for next level | SPACE to restart", True, (200, 200, 50))
            else:
                hint_surf = hint_font.render("Press SPACE to restart", True, (200, 200, 50))

            # Proportional y-spacing
            y_pos = GAMEOVER_HEIGHT * 0.1
            spacing = GAMEOVER_HEIGHT * 0.12

            for surf_item in [surf, level_surf, score_surf, highscore_surf, hint_surf]:
                gameover_screen.blit(surf_item, (GAMEOVER_WIDTH//2 - surf_item.get_width()//2, int(y_pos)))
                y_pos += spacing

            # Blit centered
            x_offset = (self.width - GAMEOVER_WIDTH) // 2
            y_offset = (self.height - GAMEOVER_HEIGHT) // 2
            screen.fill(BLACK)
            screen.blit(gameover_screen, (x_offset, y_offset))
            
            return


        # background
        screen.fill(BLACK)
        state = self.engine.get_state_snapshot()
        maze = state["maze"]

        # draw tiles
        for y in range(maze.height):
            for x in range(maze.width):
                ch = maze.get_tile(x,y)
                left = x * self.tile_size
                top = y * self.tile_size
                rect = Rect(left, top, self.tile_size, self.tile_size)


                if maze.is_wall(x,y) :
                    # pygame.draw.rect(screen, WALL_COLOR, rect)
                    pygame.draw.rect(screen, WALL_COLOR, rect)
                    # Top highlight
                    pygame.draw.line(screen, (100,100,200), (left, top), (left+self.tile_size, top), 2)
                    # Left shadow
                    pygame.draw.line(screen, (10,10,50), (left, top), (left, top+self.tile_size), 2)


                else:
                    # 
                    
                    # For normal pellets
                    if (x,y) in state["pellets"]:
                        center = (left + self.tile_size//2, top + self.tile_size//2)
                        radius = max(2, self.tile_size//8)
                        pygame.draw.circle(screen, PELLET_COLOR, center, radius)
                        # Glow effect
                        pygame.draw.circle(screen, (255, 255, 100), center, radius//2)

                    # For power pellets (pulsing)
                    if (x,y) in state["power_pellets"]:
                        center = (left + self.tile_size//2, top + self.tile_size//2)
                        size = max(4, self.tile_size//5 + int(4 * math.sin(pygame.time.get_ticks()/150)))
                        pygame.draw.circle(screen, POWER_COLOR, center, size)
                    # Glow
                        pygame.draw.circle(screen, (255,255,150), center, size//2)

        # draw Pac-Man
        pm = state["pacman"]
        if pm.x is None:
            pmx, pmy = maze.tile_center(pm.tx, pm.ty, self.tile_size)
            pm.set_pixel_pos(pmx, pmy)

        px, py = int(pm.x), int(pm.y)
        radius = self.tile_size//2 - 2

        # Mouth animation (time-based)
        current_time = pygame.time.get_ticks()
        if current_time - self.last_mouth_toggle > self.mouth_interval:
            self.mouth_open = not self.mouth_open
            self.last_mouth_toggle = current_time

        angle = 40 if self.mouth_open else 10

        # direction → angle mapping
        dx, dy = pm.direction
        if (dx, dy) == (1, 0):     # RIGHT
            start = math.radians(angle)
            end   = math.radians(360 - angle)
        elif (dx, dy) == (-1, 0):  # LEFT
            start = math.radians(180 + angle)
            end   = math.radians(180 - angle)
        elif (dx, dy) == (0, -1):  # UP
            start = math.radians(90 + angle)
            end   = math.radians(90 - angle)
        elif (dx, dy) == (0, 1):   # DOWN
            start = math.radians(270 + angle)
            end   = math.radians(270 - angle)
        else:
            # standing still → minimal mouth
            start = math.radians(5)
            end   = math.radians(355)

#----------------------------------------------------------
        # Define mouth_points safely
        mouth_points = [
            (px, py),
            (px + radius * math.cos(start), py - radius * math.sin(start)),
            (px + radius * math.cos(end),   py - radius * math.sin(end)),
        ]
#-----------------------------------------------------------------
        # Draw Pac-Man (circle)
        pygame.draw.circle(screen, PACMAN_COLOR, (px, py), radius)

# Highlight for 3D effect
        highlight_pos = (px - radius//3, py - radius//3)
        pygame.draw.circle(screen, (255,255,150), highlight_pos, radius//3)

# Draw mouth using arc for smooth cut
        if self.mouth_open:
    # Map direction to angle
            if (dx, dy) == (1, 0):     # RIGHT
                start_angle = -angle
                end_angle = angle
            elif (dx, dy) == (-1, 0):  # LEFT
                start_angle = 180 - angle
                end_angle = 180 + angle
            elif (dx, dy) == (0, -1):  # UP
                start_angle = 90 - angle
                end_angle = 90 + angle
            elif (dx, dy) == (0, 1):   # DOWN
                start_angle = 270 - angle
                end_angle = 270 + angle
            else:
                start_angle = -angle
                end_angle = angle

    # Convert to radians
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)

            mouth_rect = pygame.Rect(px - radius, py - radius, 2*radius, 2*radius)
            pygame.draw.arc(screen, BLACK, mouth_rect, start_rad, end_rad, radius//2)


#-----------------------------------------------------------------

        # Draw the mouth cutout (triangle wedge)
        mouth_points = [
            (px, py),
            (px + radius * math.cos(start), py - radius * math.sin(start)),
            (px + radius * math.cos(end),   py - radius * math.sin(end)),
        ]

        pygame.draw.polygon(screen, BLACK, mouth_points)

        # draw ghosts
        for g in state["ghosts"]:
            gx = int(g.x) if g.x is not None else maze.tile_center(g.tx, g.ty, self.tile_size)[0]
            gy = int(g.y) if g.y is not None else maze.tile_center(g.tx, g.ty, self.tile_size)[1]

            # ghost color
            if g.state == "normal":
                c = GHOST_COLOR
            else:
                # Vulnerable: flash blue when timer < 2 sec
                if g.vulnerable_timer < 2:
                    c = (50, 200, 200) if (pygame.time.get_ticks() // 250) % 2 == 0 else (255,255,255)
                else:
                    c = (50, 200, 200)

    # scale factor (70% of tile size)
            scale = 0.7
            body_width = int((self.tile_size - 2) * scale)
            body_height = int((self.tile_size - 2) * scale)
            top = gy - body_height // 2
            left = gx - body_width // 2

            # main body (rounded rectangle for smooth top)
            pygame.draw.rect(screen, c, (left, top + body_height//4, body_width, 3*body_height//4))
            pygame.draw.circle(screen, c, (gx, top + body_height//4), body_width//2)

    # wavy bottom
            wave_radius = body_width // 6
            for i in range(3):
                wave_x = left + wave_radius * (1 + 2*i)
                wave_y = top + body_height
                pygame.draw.circle(screen, c, (wave_x, wave_y), wave_radius)

    # ghost eyes
            eye_offset_x = body_width // 6
            eye_offset_y = body_height // 6
            pygame.draw.circle(screen, (255,255,255), (gx - eye_offset_x, gy - eye_offset_y), 2)  # smaller eyes
            pygame.draw.circle(screen, (255,255,255), (gx + eye_offset_x, gy - eye_offset_y), 2)

    # pupils
            pygame.draw.circle(screen, (0,0,0), (gx - eye_offset_x, gy - eye_offset_y), 1)
            pygame.draw.circle(screen, (0,0,0), (gx + eye_offset_x, gy - eye_offset_y), 1)

        # HUD
        hud_bg = Rect(0, self.engine.height_px, self.width, self.hud_height)
        pygame.draw.rect(screen, (20,20,20), hud_bg)

        # HUD background with border
        hud_bg = Rect(0, self.engine.height_px, self.width, self.hud_height)
        pygame.draw.rect(screen, (30,30,30), hud_bg)
        pygame.draw.rect(screen, (255,255,255), hud_bg, 2)  # border


        # Optional high score display
        if hasattr(self.engine, "high_scores") and self.engine.high_scores:
            hs_text = f"High Score: {max(self.engine.high_scores)}"
            screen.blit(self.font.render(hs_text, True, (255,215,0)), (400, self.engine.height_px + 8))

        # Draw HUD
        score_text = self.font.render(f"Score: {self.engine.pacman.score}", True, WHITE)
        level_text = self.font.render(f"Level: {self.engine.current_level_name.upper()}", True, (100,200,255))
        high_text = self.font.render(f"High: {self.engine.get_current_highscore()}", True, (255,215,0))

        screen.blit(score_text, (10, self.engine.height_px + 10))
        screen.blit(level_text, (self.width//2 - level_text.get_width()//2, self.engine.height_px + 10))
        screen.blit(high_text, (self.width - high_text.get_width() - 10, self.engine.height_px + 10))
