# environment/maze.py
import os
from collections import deque

# Tile constants
WALL = '#'
PELLET = '.'
POWER = 'o'
EMPTY = ' '
PACMAN = 'P'
GHOST = 'G'

# DEFAULT_MAP = [
# "%%%%%%%%%%%%%%%%%%%%",
# "%.G..%.....o..%..o.%",
# "%.%%.%.%%..%..%.%%.%",
# "%.......%..%.....%.%",
# "%.%.%%..%  %%.%%.%.%",
# "%...G....P..%.%....%",
# "%.%....%%%%.%....%.%",
# "%.%..%.%...o%.%..%.%",
# "%.%..%.% %%%%.%..%.%",
# "%.%..o........%..%.%",
# "%.%%.%.%%%%%%...%%.%",
# "%.G..%....G...%....%",
# "%%%%%%%%%%%%%%%%%%%%"
# ]


# DEFAULT_MAP = [
# "%%%%%%%%%%%%%%%%%",
# "%....%G  G%.....%",
# "%.%%..%  %%..%%.%",
# "%..o.%......%.o.%",
# "%.%%.%.%...%%.%.%",
# "%.%..o.....%..%.%",
# "%.......P.......%",
# "%%%%%%%%%%%%%%%%%"
# ]

# DEFAULT_MAP = [
# "%%%%%%%%%%%%%%%%%",
# "%......G G......%",
# "%.%..%o   o%..%.%",
# "%.%..%.....%..%.%",
# "%.%..%.....%..%.%",
# "%....%.....%....%",
# "%.%....% %....%.%",
# "%.......P.......%",
# "%%%%%%%%%%%%%%%%%"
# ]

DEFAULT_MAP = [
"%%%%%%%%%%%%%%%",
"%.....G G.....%",
"%.%.%o   o%.%.%",
"%...%.....%...%",
"%.%...% %...%.%",
"%......P......%",
"%%%%%%%%%%%%%%%"
]


class Maze:
    def __init__(self, map_lines=None):
        # map_lines: list of strings; each char represents tile
        if map_lines is None:
            map_lines = DEFAULT_MAP
        self.raw = [list(line.rstrip('\n')) for line in map_lines]
        self.height = len(self.raw)
        self.width = max(len(row) for row in self.raw)
        # normalize row lengths
        for row in self.raw:
            if len(row) < self.width:
                row += [' '] * (self.width - len(row))

    def is_wall(self, tx, ty):
        if tx < 0 or tx >= self.width or ty < 0 or ty >= self.height:
            return True
        return self.raw[ty][tx] == '%' or self.raw[ty][tx] == '#'

    def get_tile(self, tx, ty):
        if tx < 0 or tx >= self.width or ty < 0 or ty >= self.height:
            return '%'
        return self.raw[ty][tx]

    def find_all(self, char):
        out = []
        for y, row in enumerate(self.raw):
            for x, c in enumerate(row):
                if c == char:
                    out.append((x, y))
        return out

    def neighbors(self, tx, ty):
        # 4-connected neighbors (no diagonals)
        dirs = [(0,-1),(1,0),(0,1),(-1,0)]
        for dx,dy in dirs:
            nx, ny = tx+dx, ty+dy
            if 0 <= nx < self.width and 0 <= ny < self.height and not self.is_wall(nx, ny):
                yield (nx, ny)

    def bfs_distance_grid(self, starts):
        # returns dist dict from any start to all reachable tiles
        dist = {p:0 for p in starts}
        q = deque(starts)
        while q:
            x,y = q.popleft()
            for nx,ny in self.neighbors(x,y):
                if (nx,ny) not in dist:
                    dist[(nx,ny)] = dist[(x,y)] + 1
                    q.append((nx,ny))
        return dist

    def tile_center(self, tx, ty, tile_size):
        # pixel center of tile (tx,ty)
        return (tx * tile_size + tile_size // 2, ty * tile_size + tile_size // 2)
