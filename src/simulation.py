# Placeholder for Simulation class 

import pymunk
import random # For explosion velocity
from pymunk.vec2d import Vec2d # For explosion velocity
from dummy import Dummy
# Import the neural network
from neural_network import NeuralNetwork
import math

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

class Simulation:
    def __init__(self, gravity: tuple[float, float] = (0, -981.0)):
        """Initializes the simulation space, gravity, ground, laser, and collision handler.
           Manages multiple dummies and their associated neural networks.
        """
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self.laser_body: pymunk.Body | None = None
        self.laser_shape: pymunk.Shape | None = None

        # Lists to manage multiple dummies and networks
        self.dummies: list[Dummy] = []
        self.neural_networks: list[NeuralNetwork] = []
        self.dummies_dead: list[bool] = [] # Tracks if dummy[i] is dead
        self.dummy_id_to_index: dict[int, int] = {} # Map dummy.id to list index

        # Track explosion debris
        self.debris_bodies: list[pymunk.Body] = []
        self.debris_shapes: list[pymunk.Shape] = []

        self._add_ground()
        self._add_laser() # Laser is shared by all
        self._setup_collision_handler()

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
            dummy_index = self.dummy_id_to_index.get(hit_dummy.id)

            # Check if already processed (collision might trigger multiple times)
            if dummy_index is not None and not self.dummies_dead[dummy_index]:
                print(f"ZAP! Dummy {hit_dummy.id} hit by laser. Exploding!")
                
                # 1. Mark dummy as hit internally (gets position)
                explosion_center = hit_dummy.mark_as_hit()
                
                if explosion_center: 
                    # 2. Mark as logically dead for simulation steps
                    self.dummies_dead[dummy_index] = True
                    
                    # 3. Create visual explosion debris
                    self._create_explosion(explosion_center)
                    
                    # 4. Remove original dummy parts from space
                    # Must happen *after* creating explosion based on its position
                    hit_dummy.remove_from_space()
                else:
                    # Mark_as_hit returned None, likely already hit
                    pass
        else:
            print("Warning: Laser collision detected, but couldn't identify Dummy instance.")

        return True # Process collision (sensor means no physical response)

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

    def add_dummy_instance(self, position: tuple[float, float]) -> None:
        """Creates a new Dummy and its associated NeuralNetwork, adding them to the simulation."""
        new_dummy = Dummy(self.space, position, collision_type=COLLISION_TYPE_DUMMY)
        new_nn = NeuralNetwork() # Each dummy gets its own NN instance
        
        # Add to lists and tracking
        list_index = len(self.dummies)
        self.dummies.append(new_dummy)
        self.neural_networks.append(new_nn)
        self.dummies_dead.append(False) # Start alive
        self.dummy_id_to_index[new_dummy.id] = list_index

        print(f"Added Dummy {new_dummy.id} at index {list_index}")

    def step(self, dt: float) -> None:
        """Advances the simulation: updates all active dummies via NNs, then steps physics."""
        # Update motors for all *active* dummies based on their NN
        for i, dummy in enumerate(self.dummies):
            if not self.dummies_dead[i]:
                try:
                    sensor_values = dummy.get_sensor_data()
                    motor_outputs = self.neural_networks[i].activate(sensor_values)
                    dummy.set_motor_rates(motor_outputs)
                except Exception as e:
                    print(f"Error processing Dummy {dummy.id} at index {i}: {e}")
                    # Mark as dead or handle error appropriately?
                    self.dummies_dead[i] = True 

        # Step the entire physics space once
        self.space.step(dt)

        # Cleanup old debris particles
        self._cleanup_debris()

    # --- Removed Methods --- 
    # reset() method is removed - restarting logic now in main.py if needed
    # get_fitness() method is removed - fitness calculation would be per-dummy
    #                           and depends on the specific evolutionary goal. 