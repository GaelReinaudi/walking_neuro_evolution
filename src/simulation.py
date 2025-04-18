# Placeholder for Simulation class 

import pymunk
import random # For explosion velocity
from pymunk.vec2d import Vec2d # For explosion velocity
from dummy import Dummy
# NEAT imports
import neat
import math
import time # For limiting generation time

# Collision Types
COLLISION_TYPE_DUMMY = 1
COLLISION_TYPE_LASER = 2
COLLISION_TYPE_GROUND = 3
COLLISION_TYPE_DEBRIS = 4 # New type for explosion parts

LASER_SPEED = 25.0 # Pixels per second
# Adjust laser start X to be closer, e.g., just left of the typical screen view
LASER_START_X = -20
LASER_HEIGHT = 800 # Make it tall
LASER_WIDTH = 5

# Explosion Constants
NUM_DEBRIS_PARTS = 15
DEBRIS_MASS = 0.1
DEBRIS_RADIUS = 3
DEBRIS_VELOCITY_SCALE = 150 # Adjust for bigger/smaller visual explosion
DEBRIS_CLEANUP_Y = -100 # Y threshold to remove debris

# Simulation Constants
SIM_DT = 1/60.0
DEFAULT_DUMMY_START_POS = (250, 150)
GENERATION_TIME_LIMIT_SEC = 30 # Max time per generation

class Simulation:
    def __init__(self, gravity: tuple[float, float] = (0, -981.0)):
        """Initializes the simulation space, gravity, ground, laser, and collision handler.
           Manages debris cleanup and collision handling.
        """
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.laser_body: pymunk.Body | None = None
        self.laser_shape: pymunk.Shape | None = None
        self.debris_bodies: list[pymunk.Body] = []
        self.debris_shapes: list[pymunk.Shape] = []
        self.viz = None # Optional visualizer reference

        self._add_ground()
        self._add_laser() # Laser is shared by all
        self._setup_collision_handler()

    def set_visualizer(self, viz):
        """Allows associating a visualizer for drawing during run_generation."""
        self.viz = viz

    def _clear_simulation_state(self):
        """Removes all dynamic elements (dummies, debris) from the space."""
        # Remove debris first
        while self.debris_bodies:
            body = self.debris_bodies.pop()
            shape = self.debris_shapes.pop()
            if shape in self.space.shapes: self.space.remove(shape)
            if body in self.space.bodies: self.space.remove(body)
        
        # Remove any remaining dummies (important if generation ends early)
        # Need to get dummies directly from space as internal lists are cleared per-generation
        dummies_in_space = [shape.user_data for shape in self.space.shapes 
                            if hasattr(shape, 'user_data') and isinstance(shape.user_data, Dummy)]
        unique_dummies = list(set(dummies_in_space)) # Get unique dummy instances
        for dummy in unique_dummies:
            if isinstance(dummy, Dummy): # Type check
                dummy.remove_from_space()

    def _reset_laser(self):
        """Resets the laser to its starting position and velocity."""
        if self.laser_body:
            self.laser_body.position = (LASER_START_X, LASER_HEIGHT / 2)
            self.laser_body.velocity = (LASER_SPEED, 0)

    def _add_ground(self) -> None:
        """Adds a static ground segment to the simulation space."""
        ground = pymunk.Segment(self.space.static_body, (-5000, 10), (5000, 10), 5)
        ground.friction = 0.8
        ground.elasticity = 0.5
        ground.collision_type = COLLISION_TYPE_GROUND
        # Define what the ground can collide with (only Dummies, not Debris or Laser)
        ground.filter = pymunk.ShapeFilter(categories=0b100, mask=0b001)
        self.space.add(ground)

    def _add_laser(self) -> None:
        """Adds a kinematic laser beam moving from left to right."""
        self.laser_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.laser_body.position = (LASER_START_X, LASER_HEIGHT / 2)
        self.laser_body.velocity = (LASER_SPEED, 0)
        self.laser_shape = pymunk.Poly.create_box(self.laser_body, (LASER_WIDTH, LASER_HEIGHT))
        self.laser_shape.sensor = True
        self.laser_shape.collision_type = COLLISION_TYPE_LASER
        self.laser_shape.color = (255, 0, 0, 255)
         # Laser only collides with Dummies
        self.laser_shape.filter = pymunk.ShapeFilter(categories=0b1000, mask=0b001) 
        self.space.add(self.laser_body, self.laser_shape)

    def _laser_hit_dummy(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
        """Callback: Marks dummy as hit, creates explosion, removes original dummy."""
        dummy_shape = None
        for shape in arbiter.shapes:
            if shape.collision_type == COLLISION_TYPE_DUMMY:
                dummy_shape = shape
                break
        
        if dummy_shape and hasattr(dummy_shape, 'user_data') and isinstance(dummy_shape.user_data, Dummy):
            hit_dummy: Dummy = dummy_shape.user_data
            
            # Only process if not already hit
            explosion_center = hit_dummy.mark_as_hit()
            if explosion_center:
                print(f"ZAP! Dummy {hit_dummy.id} hit by laser. Exploding at {explosion_center}!")
                # Note: We don't use self.dummies_dead anymore
                self._create_explosion(explosion_center)
                hit_dummy.remove_from_space()
        else:
            print("Warning: Laser collision detected, but couldn't identify Dummy instance.")

        return True

    def _create_explosion(self, center_pos: Vec2d):
        """Creates debris particles at the given position."""
        for _ in range(NUM_DEBRIS_PARTS):
            body = pymunk.Body(DEBRIS_MASS, pymunk.moment_for_circle(DEBRIS_MASS, 0, DEBRIS_RADIUS))
            body.position = center_pos
            # Give random outward velocity
            angle = random.uniform(0, math.pi * 2)
            velocity = Vec2d(math.cos(angle), math.sin(angle)) * DEBRIS_VELOCITY_SCALE * random.uniform(0.5, 1.5)
            body.velocity = velocity
            body.angular_velocity = random.uniform(-5, 5)

            shape = pymunk.Circle(body, DEBRIS_RADIUS)
            shape.friction = 0.5
            shape.collision_type = COLLISION_TYPE_DEBRIS
            # Filter: Debris collides with nothing
            shape.filter = pymunk.ShapeFilter(categories=0b10, mask=0b0) 
            shape.color = (random.randint(150, 255), random.randint(0, 50), 0, 255) # Red-ish
            
            self.space.add(body, shape)
            self.debris_bodies.append(body)
            self.debris_shapes.append(shape)

    def _cleanup_debris(self):
        """Removes debris particles that fall below a certain threshold."""
        removed_indices = []
        for i in range(len(self.debris_bodies) - 1, -1, -1): # Iterate backwards for removal
            body = self.debris_bodies[i]
            if body.position.y < DEBRIS_CLEANUP_Y:
                shape = self.debris_shapes[i]
                if shape in self.space.shapes:
                    self.space.remove(shape)
                if body in self.space.bodies:
                     self.space.remove(body)
                removed_indices.append(i)
        
        # Remove from lists after iterating
        for index in sorted(removed_indices, reverse=True):
             del self.debris_bodies[index]
             del self.debris_shapes[index]

    def _setup_collision_handler(self) -> None:
        """Sets up the handler for laser-dummy collisions."""
        handler = self.space.add_collision_handler(COLLISION_TYPE_LASER, COLLISION_TYPE_DUMMY)
        handler.begin = self._laser_hit_dummy
        # TODO: Add handler for ground collisions if needed for sensors

    # --- Main Evaluation Loop for NEAT --- 
    def run_generation(self, genomes: list[tuple[int, neat.DefaultGenome]], config: neat.Config):
        """Runs one generation of the simulation for the given genomes.
        
        Args:
            genomes: A list of (genome_id, genome_object) tuples.
            config: The NEAT configuration object.
        """
        self._clear_simulation_state()
        self._reset_laser()
        
        dummies_this_gen: dict[int, Dummy] = {} # genome_id -> Dummy instance
        networks_this_gen: dict[int, neat.nn.FeedForwardNetwork] = {} # genome_id -> network
        active_genomes = len(genomes)
        start_time = time.time()

        # Create dummies and networks for this generation
        for genome_id, genome in genomes:
            genome.fitness = 0 # Initialize fitness
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            dummy_start_pos = (DEFAULT_DUMMY_START_POS[0], 
                               DEFAULT_DUMMY_START_POS[1] + random.uniform(-20, 20)) # Slight vertical stagger
            dummy = Dummy(self.space, dummy_start_pos, collision_type=COLLISION_TYPE_DUMMY)
            
            networks_this_gen[genome_id] = net
            dummies_this_gen[genome_id] = dummy

        # --- Simulation Loop for this Generation --- 
        while active_genomes > 0 and (time.time() - start_time) < GENERATION_TIME_LIMIT_SEC:
            # Check for visualization exit requests
            if self.viz and not self.viz.running:
                # If user closes window during eval, stop the generation early
                 print("Visualizer closed, ending generation early.")
                 break

            # Update NNs and step physics
            current_active = 0
            for genome_id, genome in genomes:
                dummy = dummies_this_gen.get(genome_id)
                if dummy and not dummy.is_hit:
                    current_active += 1
                    try:
                        net = networks_this_gen[genome_id]
                        sensor_values = dummy.get_sensor_data()
                        motor_outputs = net.activate(sensor_values)
                        dummy.set_motor_rates(motor_outputs)
                    except Exception as e:
                        print(f"Error activating network for genome {genome_id} (Dummy {dummy.id}): {e}")
                        # Mark as hit on error?
                        hit_pos = dummy.mark_as_hit()
                        if hit_pos: self._create_explosion(hit_pos)
                        dummy.remove_from_space() # Remove on error
                        
            # Update active count
            active_genomes = current_active

            # Step physics
            self.space.step(SIM_DT)

            # Cleanup debris
            self._cleanup_debris()

            # Update visualization if attached
            if self.viz:
                if not self.viz.draw(self):
                    # Stop generation if visualizer quit
                    active_genomes = 0 # Ensure loop terminates
                    break 
            
        # --- End of Generation Loop --- 
        print(f"Generation finished. Time: {time.time() - start_time:.2f}s. Active dummies remaining: {active_genomes}")

        # Calculate fitness for all genomes in this generation
        for genome_id, genome in genomes:
            dummy = dummies_this_gen.get(genome_id)
            if dummy:
                # Fitness = distance moved left
                # Use final_x if hit, otherwise current position
                final_x = dummy.final_x if dummy.final_x is not None else dummy.get_body_position().x
                fitness = dummy.initial_position.x - final_x
                genome.fitness = fitness if fitness is not None else -100 # Penalize errors severely
                # print(f"Genome {genome_id}, Dummy {dummy.id}, Final X: {final_x:.2f}, Fitness: {genome.fitness:.2f}")
            else:
                 # Should not happen if setup is correct
                 genome.fitness = -1000 
                 print(f"Error: Dummy not found for genome {genome_id} during fitness calculation.")

    # --- Removed Methods --- 
    # reset() method is removed - restarting logic now in main.py if needed
    # get_fitness() method is removed - fitness calculation would be per-dummy
    #                           and depends on the specific evolutionary goal. 