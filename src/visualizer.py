import pygame
import pymunk
import pymunk.pygame_util
import os
import random  # Import Python's random module
# Assuming simulation.py is in the same parent directory (src)
from simulation import Simulation # Needed to access dummy position

# Try to import the network visualizer, but continue if it fails
try:
    from network_viz import NetworkVisualizer
    NETWORK_VIZ_AVAILABLE = True
except ImportError:
    print("Warning: NetworkVisualizer module not found. Neural network visualization will be disabled.")
    NETWORK_VIZ_AVAILABLE = False

# Constants for camera
CAMERA_Y_OFFSET = 0  # Increased to focus higher on the action
ZOOM_FACTOR = 4  # Increased zoom factor for more detail

class Visualizer:
    def __init__(self, width: int = 3200, height: int = 800, fps: int = 30):
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
        
        # Initialize fonts for stats display
        self.font = pygame.font.SysFont("Arial", 24)
        self.header_font = pygame.font.SysFont("Arial", 28, bold=True)
        
        # Stats data
        self.stats = {
            "generation": 0,
            "best_fitness": 0.0,
            "avg_fitness": 0.0,
            "active_dummies": 0,
            "species_count": 0,
            "time_elapsed": 0.0,
            "species_sizes": []
        }
        
        # Initialize neural network visualizer
        if NETWORK_VIZ_AVAILABLE:
            self.network_viz = NetworkVisualizer(width=400, height=500)
        else:
            self.network_viz = None
        
        # Store best genome for visualization
        self.best_genome = None
        self.neat_config = None
        
        # Toggle for network display - ON by default to show it right away
        self.show_network = True
        
        # Camera should be fixed until laser reaches this x coordinate
        self.camera_pan_threshold = 120
        
        # Create a texture for the ground
        self.ground_texture = self._create_ground_texture()
        
        # Load face image
        face_path = os.path.join("images", "face.png")
        try:
            self.face_image = pygame.image.load(face_path)
            # Scale the image much larger - twice as big as before
            self.face_image = pygame.transform.scale(self.face_image, (72, 72))
            self.face_loaded = True
            print(f"Face image loaded from {face_path}")
        except Exception as e:
            print(f"Failed to load face image: {e}")
            self.face_loaded = False

    def _create_ground_texture(self, width=200, height=20):
        """Create a repeatable texture for the ground."""
        texture = pygame.Surface((width, height), pygame.SRCALPHA)
        # Fill with base color
        texture.fill((150, 150, 150))
        
        # Add some texture details
        for i in range(0, width, 10):
            # Alternate dark and light stripes
            color = (100, 100, 100) if i % 20 == 0 else (180, 180, 180)
            pygame.draw.line(texture, color, (i, 0), (i, height), 2)
            
        # Add horizontal lines
        for i in range(0, height, 5):
            pygame.draw.line(texture, (130, 130, 130), (0, i), (width, i), 1)
            
        # Add some random dots for texture
        for _ in range(100):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            pygame.draw.circle(texture, (90, 90, 90), (int(x), int(y)), 1)
            
        return texture

    def update_stats(self, stats_dict: dict):
        """Update the stats to be displayed on screen."""
        self.stats.update(stats_dict)
        
    def set_best_genome(self, genome, config):
        """Set the best genome for neural network visualization."""
        self.best_genome = genome
        self.neat_config = config

    def process_events(self) -> None:
        """Handles Pygame events, like closing the window."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("User closed the visualization window")
                self._running = False
                return False  # Signal immediate exit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("User pressed ESC, closing visualization")
                    self._running = False
                    return False  # Signal immediate exit
                elif event.key == pygame.K_n and NETWORK_VIZ_AVAILABLE:
                    # Toggle network visualization
                    self.show_network = not self.show_network
                    print(f"Neural network visualization: {'ON' if self.show_network else 'OFF'}")
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
        # Get the laser position directly from simulation
        laser_x = 0
        if hasattr(sim, 'laser_body') and sim.laser_body:
            laser_x = sim.laser_body.position.x
        
        # Explicitly force camera to follow laser after threshold
        if laser_x >= self.camera_pan_threshold:
            # Camera follows laser position - this is what creates the panning effect
            self.camera_offset_x = laser_x - self.camera_pan_threshold
        else:
            # Fixed position at start
            self.camera_offset_x = 0

        # Fixed Y offset to keep ground visible
        self.camera_offset_y = CAMERA_Y_OFFSET

        # --- Prepare Transformation ---
        # Create the transformation matrix with zoom and camera offset
        cam_transform = pymunk.Transform.translation(-self.camera_offset_x, -self.camera_offset_y)
        # Apply zoom 
        scale = self.zoom
        cam_transform = pymunk.Transform(scale, 0, 0, scale, cam_transform.tx * scale, cam_transform.ty * scale)
        # Apply to draw options
        self.draw_options.transform = cam_transform

        # --- Draw Scene --- 
        # Clear screen
        self.screen.fill(pygame.Color("lightblue"))
        
        # Draw textured ground before the physics objects
        ground_y = 0  # Ground height in world coordinates
        texture_width = self.ground_texture.get_width()
        
        # Draw repeating ground texture along the full width
        world_width = 2000  # Some large value for the world width
        screen_ground_y = (ground_y - self.camera_offset_y) * self.zoom
        
        for x in range(0, world_width, texture_width):
            screen_x = (x - self.camera_offset_x) * self.zoom
            if 0 <= screen_x <= self.width:
                self.screen.blit(self.ground_texture, (screen_x, screen_ground_y))

        # Draw a vertical red line at x=100 (in world coordinates) for threshold marker
        x_marker = 100
        screen_x = (x_marker - self.camera_offset_x) * self.zoom
        pygame.draw.line(
            self.screen,
            (255, 0, 0),  # Red
            (screen_x, 0),
            (screen_x, self.height),
            3
        )

        # Draw the space with physics objects
        sim.space.debug_draw(self.draw_options)
        
        # Draw face images on dummies (before flipping the screen)
        if self.face_loaded:
            self._draw_dummy_faces(sim)
        
        # Flip screen vertically (Pymunk Y is inverted relative to Pygame)
        flipped_surface = pygame.transform.flip(self.screen, False, True)
        self.screen.blit(flipped_surface, (0, 0))
        
        # Draw stats and UI elements (after the flip, so they're not flipped)
        self._draw_stats()
        
        # Always show the instruction for toggling network view
        if NETWORK_VIZ_AVAILABLE:
            status = "ON" if self.show_network else "OFF"
            toggle_text = self.font.render(f"Press 'N' to toggle network view (currently {status})", True, (30, 30, 30))
            self.screen.blit(toggle_text, (25, 25))
        
        # Draw neural network visualization if enabled
        if self.show_network and NETWORK_VIZ_AVAILABLE and self.network_viz and self.best_genome and self.neat_config:
            try:
                network_surface = self.network_viz.draw_network(self.best_genome, self.neat_config)
                # Position in top left corner with some padding
                self.screen.blit(network_surface, (20, 60))
            except Exception as e:
                print(f"Error drawing neural network: {e}")
                # Disable network visualization on error
                self.show_network = False

        # Update display
        pygame.display.flip()

        # Cap the frame rate
        self.clock.tick(self.fps)

        return True # Continue running
    
    def _draw_dummy_faces(self, sim):
        """Draw face images on all dummies in the simulation."""
        if not self.face_loaded:
            return
        
        # Find all dummies in the simulation
        dummies = []
        for shape in sim.space.shapes:
            if hasattr(shape, 'user_data') and hasattr(shape.user_data, 'head'):
                dummy = shape.user_data
                if dummy not in dummies and hasattr(dummy, 'head') and not dummy.is_hit:
                    dummies.append(dummy)
        
        # Draw face on each dummy's head
        for dummy in dummies:
            # Get the head position in world coordinates
            head_pos = dummy.head.position
            
            # Convert to screen coordinates with camera transform
            screen_x = (head_pos.x - self.camera_offset_x) * self.zoom
            screen_y = (head_pos.y - self.camera_offset_y) * self.zoom
            
            # Convert rotation angle (radians to degrees)
            # Add 180 degrees to fix upside-down orientation
            rotation_angle = -dummy.head.angle * 180.0 / 3.14159 + 180
            
            # Rotate the face image to match the head's rotation
            rotated_face = pygame.transform.rotate(self.face_image, rotation_angle)
            
            # Center the image on the head position
            rot_width = rotated_face.get_width()
            rot_height = rotated_face.get_height()
            screen_x -= rot_width / 2
            screen_y -= rot_height / 2
            
            # Blit the face image
            self.screen.blit(rotated_face, (screen_x, screen_y))
    
    def _draw_stats(self):
        """Draw evolution stats on the right side of the screen."""
        # Stats panel background
        panel_width = 350
        panel_x = self.width - panel_width
        panel_rect = pygame.Rect(panel_x, 0, panel_width, self.height)
        pygame.draw.rect(self.screen, (30, 30, 30, 200), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)
        
        # Header
        title = self.header_font.render("NEAT Evolution Stats", True, (220, 220, 220))
        self.screen.blit(title, (panel_x + 10, 20))
        
        # Draw horizontal line
        pygame.draw.line(self.screen, (200, 200, 200), 
                         (panel_x + 5, 60), 
                         (panel_x + panel_width - 5, 60), 2)
        
        # Core stats
        y_pos = 80
        line_height = 35
        
        stats_to_display = [
            ("Generation:", f"{self.stats['generation']}"),
            ("Best Fitness:", f"{self.stats['best_fitness']:.2f}"),
            ("Avg Fitness:", f"{self.stats['avg_fitness']:.2f}"),
            ("Active Dummies:", f"{self.stats['active_dummies']}"),
            ("Species Count:", f"{self.stats['species_count']}"),
            ("Time Elapsed:", f"{self.stats['time_elapsed']:.2f}s")
        ]
        
        for label, value in stats_to_display:
            label_surf = self.font.render(label, True, (220, 220, 220))
            value_surf = self.font.render(value, True, (255, 255, 100))
            self.screen.blit(label_surf, (panel_x + 15, y_pos))
            self.screen.blit(value_surf, (panel_x + 210, y_pos))
            y_pos += line_height
        
        # Draw horizontal line
        pygame.draw.line(self.screen, (200, 200, 200), 
                         (panel_x + 5, y_pos), 
                         (panel_x + panel_width - 5, y_pos), 2)
        
        # Species breakdown header
        y_pos += 20
        species_header = self.header_font.render("Species Sizes", True, (220, 220, 220))
        self.screen.blit(species_header, (panel_x + 10, y_pos))
        y_pos += 40
        
        # Species breakdown
        for i, (species_id, size, stagnation) in enumerate(self.stats.get('species_sizes', [])):
            if i > 8:  # Limit to showing 9 species
                more_text = self.font.render(f"... and {len(self.stats['species_sizes']) - 9} more", 
                                            True, (180, 180, 180))
                self.screen.blit(more_text, (panel_x + 15, y_pos))
                break
                
            color = (180, 180, 180)
            if stagnation > 10:  # Highlight stagnating species
                color = (220, 150, 150)
                
            species_text = self.font.render(f"Species {species_id}: {size} members (stag: {stagnation})", 
                                          True, color)
            self.screen.blit(species_text, (panel_x + 15, y_pos))
            y_pos += 30

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

    def _draw_network(self, surface, genome, config):
        """Draw the neural network visualization on the provided surface."""
        try:
            if not NETWORK_VIZ_AVAILABLE or not self.network_viz or not genome or not config:
                return False

            # Get the network visualization as a surface
            network_surface = self.network_viz.draw_network(genome, config)
            if network_surface:
                # Position in top left corner with some padding
                surface.blit(network_surface, (20, 60))
                return True
            return False
        except Exception as e:
            print(f"Error drawing neural network: {e}")
            return False

    def update(self):
        """Update the visualization."""
        if not self._running:
            return False

        self.handle_events()
        self.screen.fill((240, 240, 240))  # light grey background
        
        # Draw physics objects
        self._draw_physics_objects()
        
        # Draw neural network visualization
        self._draw_network(self.screen, self.best_genome, self.neat_config)
        
        # Update display
        pygame.display.flip()
        
        return self._running 