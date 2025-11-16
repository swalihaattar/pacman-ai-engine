import numpy as np
from utils.math_utils import manhattan

class FeatureExtractor:
    """
    Converts game state into a vector of useful features.
    Used by controller for decision making.
    """

    def extract(self, engine):
        pac = engine.pacman
        ghosts = engine.ghosts
        # Corrected: combine normal and power pellets
        pellets = engine.pellets | engine.power_pellets

        # Distances to all ghosts
        ghost_dists = [manhattan((pac.tx, pac.ty), (g.tx, g.ty)) for g in ghosts]
        min_ghost_dist = min(ghost_dists) if ghost_dists else 99

        # Distances to pellets
        pellet_dists = [manhattan((pac.tx, pac.ty), p) for p in pellets]
        min_pellet_dist = min(pellet_dists) if pellet_dists else 0

        # Count pellets left
        pellet_count = len(pellets)

        return {
            "min_ghost_dist": min_ghost_dist,
            "min_pellet_dist": min_pellet_dist,
            "pellet_count": pellet_count,
            "ghost_positions": [(g.tx, g.ty) for g in ghosts],
            "pacman": (pac.tx, pac.ty)
        }
