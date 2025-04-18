import pygame
import pymunk
import pymunk.pygame_util
# Assuming simulation.py is in the same parent directory (src)
from simulation import Simulation # Needed to access dummy position

# Constants for camera
CAMERA_Y_OFFSET = -50 # How much space below the ground (0) to show
# CAMERA_X_FOLLOW_FACTOR = 0.3 # No longer following dummy

class Visualizer:
    def __init__(self, width: int = 1200, height: int = 350, fps: int = 60):
        """Initializes Pygame and sets up the display window."""
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Walking Neuro-Evolution Simulation")
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        # Adjust draw_options flags if needed (e.g., draw_options.flags |= pymunk.SpaceDebugDrawOptions.DRAW_COLLISION_POINTS)
        self.fps = fps
        self.width = width
        self.height = height
        self._running = True
        self.camera_offset_x = 0
        self.camera_offset_y = CAMERA_Y_OFFSET

    def process_events(self) -> None:
        """Handles Pygame events, like closing the window."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._running = False

    def draw(self, sim: Simulation) -> bool:
        """Clears the screen, updates camera, draws the Pymunk space, and updates the display.

        Args:
            sim: The Simulation object (contains space and laser position).

        Returns:
            False if the user quit, True otherwise.
        """
        self.process_events()
        if not self._running:
            return False

        # --- Update Camera --- 
        # Follow the laser horizontally, keeping it near the left edge
        if sim.laser_body:
             # Adjust target_x calculation to keep laser near left (e.g., 10% from edge)
            target_x = sim.laser_body.position.x - self.width * 0.10
            self.camera_offset_x = target_x # Direct follow for now
        # else: # Optional: if laser doesn't exist yet, center on 0? 
        #     self.camera_offset_x = -self.width * 0.5 

        # Fixed Y offset to keep ground visible
        self.camera_offset_y = CAMERA_Y_OFFSET

        # Create the transformation matrix
        # Pymunk positive Y is up, Pygame positive Y is down.
        # Pygame also draws from top-left. Pymunk default origin is bottom-left.
        # Need translation AND scaling (to flip Y)
        cam_transform = pymunk.Transform.translation(-self.camera_offset_x, -self.camera_offset_y)
        # We handle the Y-flip later by flipping the final surface
        self.draw_options.transform = cam_transform

        # --- Draw --- 
        # Clear screen
        self.screen.fill(pygame.Color("lightblue"))

        # Draw the space using the updated transform
        sim.space.debug_draw(self.draw_options)

        # Flip screen vertically (Pygame Y is inverted relative to Pymunk)
        flipped_surface = pygame.transform.flip(self.screen, False, True)
        self.screen.blit(flipped_surface, (0, 0))

        # Update display
        pygame.display.flip()

        # Cap the frame rate
        self.clock.tick(self.fps)

        return True # Continue running

    def close(self) -> None:
        """Shuts down Pygame."""
        pygame.quit()

    @property
    def running(self) -> bool:
        """Returns whether the visualization loop should continue."""
        return self._running 