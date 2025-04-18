import pygame
import pymunk
import pymunk.pygame_util
# Assuming simulation.py is in the same parent directory (src)
from simulation import Simulation # Needed to access dummy position

# Constants for camera
CAMERA_Y_OFFSET = 0  # Increased to focus higher on the action
ZOOM_FACTOR = 2.5  # Increased zoom factor for more detail

class Visualizer:
    def __init__(self, width: int = 2400, height: int = 700, fps: int = 60):
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
        self.zoom = ZOOM_FACTOR

    def process_events(self) -> None:
        """Handles Pygame events, like closing the window."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("User closed the visualization window")
                self._running = False
                return False  # Signal immediate exit
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print("User pressed ESC, closing visualization")
                self._running = False
                return False  # Signal immediate exit
        return True  # Continue execution

    def draw(self, sim: Simulation) -> bool:
        """Clears the screen, updates camera, draws the Pymunk space, and updates the display.

        Args:
            sim: The Simulation object (contains space and laser position).

        Returns:
            False if the user quit, True otherwise.
        """
        # Process events first and check if we should exit immediately
        if not self.process_events():
            return False
            
        if not self._running:
            return False

        # --- Update Camera --- 
        # Find the rightmost dummy
        rightmost_x = None
        rightmost_dummy = None
        
        # Find all dummies in the space
        dummies_in_space = [shape.user_data for shape in sim.space.shapes 
                          if hasattr(shape, 'user_data') and hasattr(shape.user_data, 'get_body_position')]
        
        # Get unique dummy instances
        unique_dummies = list(set(dummies_in_space))
        
        # Find the rightmost one
        for dummy in unique_dummies:
            pos = dummy.get_body_position()
            if rightmost_x is None or pos.x > rightmost_x:
                rightmost_x = pos.x
                rightmost_dummy = dummy
        
        # Camera follows the rightmost dummy if one exists, otherwise fallback to laser
        if rightmost_dummy:
            target_x = rightmost_dummy.get_body_position().x - (self.width * 0.25) / self.zoom  # Adjusted to position dummy more to the left
            self.camera_offset_x = target_x
        elif sim.laser_body:
            # Fallback to laser if no dummies exist
            target_x = sim.laser_body.position.x - (self.width * 0.02) / self.zoom  # Keep laser closer to the left edge
            self.camera_offset_x = target_x

        # Fixed Y offset to keep ground visible
        self.camera_offset_y = CAMERA_Y_OFFSET

        # Create the transformation matrix with zoom
        # Pymunk positive Y is up, Pygame positive Y is down.
        # Pygame also draws from top-left. Pymunk default origin is bottom-left.
        # Need translation AND scaling (to flip Y)
        cam_transform = pymunk.Transform.translation(-self.camera_offset_x, -self.camera_offset_y)
        # Apply zoom by creating a scaling transform and combining with translation
        scale = self.zoom
        cam_transform = pymunk.Transform(scale, 0, 0, scale, cam_transform.tx, cam_transform.ty)
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
        print("Closing Pygame visualizer...")
        self._running = False
        try:
            pygame.quit()
        except Exception as e:
            print(f"Error while closing Pygame: {e}")

    @property
    def running(self) -> bool:
        """Returns whether the visualization loop should continue."""
        return self._running 