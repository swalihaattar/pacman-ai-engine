# ai_modules/controller.py
from .feature_extractor import FeatureExtractor

class HybridController:
    """
    Hybrid AI Controller for Pacman:
    Uses features from the game to decide the next move.
    """

    def __init__(self):
        self.feature_extractor = FeatureExtractor()

    def choose_action(self, engine):
        """
        Decide Pacman's next move based on the current game engine state.
        Returns (dx, dy) move tuple.
        """
        features = self.feature_extractor.extract(engine)

        # Simple rule-based logic (demo)
        pac_x, pac_y = features["pacman"]
        ghost_positions = features["ghost_positions"]
        min_ghost_dist = features["min_ghost_dist"]
        min_pellet_dist = features["min_pellet_dist"]
        pellets_left = features["pellet_count"]

        # Avoid ghosts if too close
        if min_ghost_dist <= 1:
            # Move away from closest ghost
            gx, gy = ghost_positions[0]  # closest ghost
            dx = pac_x - gx
            dy = pac_y - gy
            # normalize to one step
            if abs(dx) > abs(dy):
                dx = 1 if dx > 0 else -1
                dy = 0
            else:
                dy = 1 if dy > 0 else -1
                dx = 0
            return dx, dy

        # Otherwise, move toward nearest pellet (very simple greedy)
        # Get all pellets (normal + power)
        pellets = engine.pellets | engine.power_pellets
        if not pellets:
            return 0, 0  # no move

        # Find closest pellet
        closest = min(pellets, key=lambda p: abs(p[0]-pac_x)+abs(p[1]-pac_y))
        dx = closest[0] - pac_x
        dy = closest[1] - pac_y

        # normalize to one step
        if abs(dx) > abs(dy):
            dx = 1 if dx > 0 else -1
            dy = 0
        elif abs(dy) > 0:
            dy = 1 if dy > 0 else -1
            dx = 0
        else:
            dx, dy = 0, 0

        return dx, dy
