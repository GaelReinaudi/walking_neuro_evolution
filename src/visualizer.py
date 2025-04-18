import pygame
import pymunk
import pymunk.pygame_util

class Visualizer:
    def __init__(self, width: int = 1200, height: int = 800, fps: int = 60):
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

    def process_events(self) -> None:
        """Handles Pygame events, like closing the window."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._running = False

    def draw(self, space: pymunk.Space) -> bool:
        """Clears the screen, draws the Pymunk space, and updates the display.

        Args:
            space: The Pymunk space object to draw.

        Returns:
            False if the user quit, True otherwise.
        """
        self.process_events()
        if not self._running:
            return False

        # Clear screen
        self.screen.fill(pygame.Color("lightblue"))

        # Draw the space
        space.debug_draw(self.draw_options)

        # Flip screen vertically (Pygame Y is inverted)
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