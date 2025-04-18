# Placeholder for Simulation class 

import pymunk
from dummy import Dummy
# Import the neural network
from neural_network import NeuralNetwork

# Collision Types
COLLISION_TYPE_DUMMY = 1
COLLISION_TYPE_LASER = 2
COLLISION_TYPE_GROUND = 3

LASER_SPEED = 25.0 # Pixels per second
# Adjust laser start X to be closer, e.g., just left of the typical screen view
LASER_START_X = -20
LASER_HEIGHT = 800 # Make it tall
LASER_WIDTH = 5

class Simulation:
    def __init__(self, gravity: tuple[float, float] = (0, -981.0)):
        """Initializes the simulation space, gravity, ground, laser, NN, and collision handler."""
        self.space = pymunk.Space()
        self.space.gravity = gravity
        self._add_ground()
        self.dummy: Dummy | None = None
        self.laser_body: pymunk.Body | None = None
        self.laser_shape: pymunk.Shape | None = None
        self.dummy_is_dead = False # Flag for laser collision
        # Instantiate the neural network
        self.nn = NeuralNetwork() # Using default sensor/motor counts

        self._add_laser()
        self._setup_collision_handler()
        # TODO: Add handler for dummy foot <-> ground contact

    def _add_ground(self) -> None:
        """Adds a static ground segment to the simulation space."""
        ground = pymunk.Segment(self.space.static_body, (-5000, 10), (5000, 10), 5)
        ground.friction = 0.8
        ground.elasticity = 0.5
        ground.collision_type = COLLISION_TYPE_GROUND # Assign collision type
        self.space.add(ground)

    def _add_laser(self) -> None:
        """Adds a kinematic laser beam moving from left to right."""
        # Kinematic bodies are moved manually (by setting velocity), not affected by gravity/collisions
        self.laser_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        # Position it vertically centered, starting off-screen
        self.laser_body.position = (LASER_START_X, LASER_HEIGHT / 2)
        self.laser_body.velocity = (LASER_SPEED, 0) # Move right

        # Create the shape (thin rectangle)
        self.laser_shape = pymunk.Poly.create_box(self.laser_body, (LASER_WIDTH, LASER_HEIGHT))
        self.laser_shape.sensor = True # Make it a sensor so it doesn't physically push things
        self.laser_shape.collision_type = COLLISION_TYPE_LASER
        self.laser_shape.color = (255, 0, 0, 255) # Red color for visualization

        self.space.add(self.laser_body, self.laser_shape)

    def _laser_hit_dummy(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
        """Callback function for laser-dummy collision."""
        print("ZAP! Dummy hit by laser.")
        self.dummy_is_dead = True
        # Stop the laser's movement after hit (optional)
        if self.laser_body:
            self.laser_body.velocity = (0, 0)
        return True # Process collision (though sensor means no physical response)

    def _setup_collision_handler(self) -> None:
        """Sets up the handler to call _laser_hit_dummy when laser hits dummy."""
        handler = self.space.add_collision_handler(COLLISION_TYPE_LASER, COLLISION_TYPE_DUMMY)
        handler.begin = self._laser_hit_dummy
        # TODO: Add handler for ground collisions (COLLISION_TYPE_GROUND, COLLISION_TYPE_DUMMY)
        # to update dummy.r_foot_contact, dummy.l_foot_contact

    def add_dummy(self, position: tuple[float, float] = (100, 100)) -> Dummy:
        """Creates and adds a Dummy to the simulation.

        Args:
            position: The starting (x, y) coordinates for the dummy's body center.

        Returns:
            The created Dummy instance.
        """
        if self.dummy is not None:
            # For simplicity now, we assume only one dummy.
            # In a more complex scenario, might need to remove the old one first.
            print("Warning: Replacing existing dummy.")
            # TODO: Proper cleanup if dummy is replaced (remove old bodies/shapes/joints)
            pass
        self.dummy = Dummy(self.space, position, collision_type=COLLISION_TYPE_DUMMY)
        return self.dummy

    def step(self, dt: float) -> None:
        """Advances the simulation by one time step, including NN activation."""
        # Only update and step if the dummy isn't dead
        if self.dummy and not self.dummy_is_dead:
            # 1. Get sensor data from dummy
            sensor_values = self.dummy.get_sensor_data()

            # 2. Activate neural network
            motor_outputs = self.nn.activate(sensor_values)

            # 3. Apply motor outputs to dummy
            self.dummy.set_motor_rates(motor_outputs)

            # 4. Step physics
            self.space.step(dt)
        elif self.dummy_is_dead:
            # If dead, maybe just step physics without NN update? (Optional)
            self.space.step(dt) # Allow body to fall naturally after death

    def reset(self, dummy_start_pos: tuple[float, float]) -> None:
        """Resets the simulation, including dummy, laser, and flags."""
        # Remove old dummy if it exists
        if self.dummy is not None:
            self.dummy.remove_from_space()
            self.dummy = None

        # Reset laser
        if self.laser_body is not None:
            self.laser_body.position = (LASER_START_X, LASER_HEIGHT / 2)
            self.laser_body.velocity = (LASER_SPEED, 0)

        # Reset flags
        self.dummy_is_dead = False

        # Reset NN state if needed (not for placeholder)
        # self.nn.reset() # If the NN had internal state

        # Add new dummy
        self.add_dummy(dummy_start_pos)

    def get_fitness(self) -> float:
        """Calculates fitness based on the dummy's horizontal position.

        Fitness is defined as the distance moved to the left from the starting x-position.
        If the dummy was hit by the laser, the fitness calculation still proceeds,
        but the simulation run would have ended earlier.

        Returns:
            The calculated fitness score.

        Raises:
            ValueError: If the dummy has not been added to the simulation yet.
        """
        if self.dummy is None:
            raise ValueError("Cannot get fitness before adding a dummy.")

        # If hit by laser, the simulation ends early. Fitness is often penalized
        # in the calling code (e.g., by considering the shorter duration).
        # We don't modify the calculation here, just note the flag is set.
        # if self.dummy_is_dead:
        #     print("(Fitness calculated after being hit by laser)")

        initial_x = self.dummy.initial_position.x
        current_x = self.dummy.get_body_position().x
        return initial_x - current_x 