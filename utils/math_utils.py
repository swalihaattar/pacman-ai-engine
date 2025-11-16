# math_utils.py
# Distance, BFS, and helper functions

def manhattan(a, b):
    """Manhattan distance between two points a=(x1,y1), b=(x2,y2)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a, b):
    """Euclidean distance."""
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2)**0.5


def bfs_distance_grid(maze, starts):
    """
    BFS distance from multiple start points.
    maze: object with neighbors(tx, ty) method
    starts: list of (x,y)
    """
    from collections import deque
    dist = {p: 0 for p in starts}
    q = deque(starts)
    while q:
        x, y = q.popleft()
        for nx, ny in maze.neighbors(x, y):
            if (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist
