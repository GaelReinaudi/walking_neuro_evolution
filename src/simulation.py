# Placeholder for Simulation class 

import pymunk
import random # For explosion velocity
from pymunk.vec2d import Vec2d # For explosion velocity
from dummy import Dummy
# NEAT imports
import neat
import math
import time # For limiting generation time
import os
import concurrent.futures
import copy

# Collision Types
COLLISION_TYPE_DUMMY = 1
COLLISION_TYPE_LASER = 2
COLLISION_TYPE_GROUND = 3
COLLISION_TYPE_DEBRIS = 4 # New type for explosion parts

LASER_SPEED = 150.0 # Pixels per second - doubled for faster laser movement
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
GENERATION_TIME_LIMIT_SEC = float('inf')  # No time limit

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

    def _clear_simulation_state(self, remove_dummies=True):
        """Removes all dynamic elements from the space."""
        # Remove debris first
        while self.debris_bodies:
            body = self.debris_bodies.pop()
            shape = self.debris_shapes.pop()
            if shape in self.space.shapes: self.space.remove(shape)
            if body in self.space.bodies: self.space.remove(body)
        
        # Remove any remaining dummies if requested
        if remove_dummies:
            # Need to get dummies directly from space
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
                # print(f"ZAP! Dummy {hit_dummy.id} hit by laser. Exploding at {explosion_center}!")
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
        
        # Add ground collision handler to detect foot and hand contacts
        ground_dummy_handler = self.space.add_collision_handler(COLLISION_TYPE_GROUND, COLLISION_TYPE_DUMMY)
        ground_dummy_handler.begin = self._ground_dummy_collision
        ground_dummy_handler.separate = self._ground_dummy_separate

    def _ground_dummy_collision(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
        """Callback for ground-dummy collisions to detect foot and hand contacts."""
        dummy_shape = None
        for shape in arbiter.shapes:
            if shape.collision_type == COLLISION_TYPE_DUMMY:
                dummy_shape = shape
                break
                
        if dummy_shape and hasattr(dummy_shape, 'user_data') and isinstance(dummy_shape.user_data, Dummy):
            dummy: Dummy = dummy_shape.user_data
            
            # Determine which part is colliding based on the body
            if dummy_shape.body == dummy.head:
                # Kill the dummy if its head touches the ground
                hit_pos = dummy.mark_as_hit()
                if hit_pos:
                    # print(f"CRASH! Dummy {dummy.id} died from head collision with ground at x={hit_pos.x:.2f}!")
                    self._create_explosion(hit_pos)
                    dummy.remove_from_space()
                return True
            elif dummy_shape.body == dummy.r_lower_leg:  # Now checking lower leg for foot contact
                dummy.r_foot_contact = True
            elif dummy_shape.body == dummy.l_lower_leg:  # Now checking lower leg for foot contact
                dummy.l_foot_contact = True
            elif dummy_shape.body == dummy.r_arm:
                dummy.r_hand_contact = True
            elif dummy_shape.body == dummy.l_arm:
                dummy.l_hand_contact = True
                
        return True
        
    def _ground_dummy_separate(self, arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
        """Callback for when a dummy part separates from the ground."""
        dummy_shape = None
        for shape in arbiter.shapes:
            if shape.collision_type == COLLISION_TYPE_DUMMY:
                dummy_shape = shape
                break
                
        if dummy_shape and hasattr(dummy_shape, 'user_data') and isinstance(dummy_shape.user_data, Dummy):
            dummy: Dummy = dummy_shape.user_data
            
            # Determine which part is separating based on the body
            if dummy_shape.body == dummy.r_lower_leg:  # Now checking lower leg for foot contact
                dummy.r_foot_contact = False
            elif dummy_shape.body == dummy.l_lower_leg:  # Now checking lower leg for foot contact
                dummy.l_foot_contact = False
            elif dummy_shape.body == dummy.r_arm:
                dummy.r_hand_contact = False
            elif dummy_shape.body == dummy.l_arm:
                dummy.l_hand_contact = False
                
        return True

    # --- Main Evaluation Loop for NEAT --- 
    def run_generation(self, genomes: list[tuple[int, neat.DefaultGenome]], config: neat.Config):
        """Runs one generation of the simulation for the given genomes.
        
        Args:
            genomes: A list of (genome_id, genome_object) tuples.
            config: The NEAT configuration object.
        """
        self._clear_simulation_state()
        self._reset_laser()
        
        # Track previous fitness for comparison
        previous_fitness = {genome_id: genome.fitness for genome_id, genome in genomes}
        
        start_time = time.time()
        
        # Check if we should use parallel processing or visualization
        if self.viz and self.viz.running:
            # Run with visualization (no parallel processing)
            print("Running with visualization (no parallel processing)")
            results = self._run_visual_simulation(genomes, config)
        else:
            # Run with parallel processing (no visualization)
            # Determine CPU count for parallel processing
            cpu_count = os.cpu_count()
            num_processes = max(1, cpu_count - 1) if cpu_count else 4  # Leave 1 CPU free
            print(f"Using {num_processes} processes for parallel simulation")
            
            # Prepare inputs for parallel processing
            genome_configs = [(genome_id, genome, config) for genome_id, genome in genomes]
            
            # Run simulations in parallel
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
                futures = [executor.submit(self._simulate_dummy, gc) for gc in genome_configs]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Process results
        fitness_values = {}
        survival_frames = {}
        movement_distances = {}
        head_stability = {}
        
        for result in results:
            genome_id, fitness, frames, distance, stability = result
            fitness_values[genome_id] = fitness
            survival_frames[genome_id] = frames
            movement_distances[genome_id] = distance
            head_stability[genome_id] = stability
            
            # Assign fitness back to genomes
            for gid, genome in genomes:
                if gid == genome_id:
                    genome.fitness = fitness
                    break
        
        total_sim_time = time.time() - start_time
        print(f"Generation finished. Time: {total_sim_time:.2f}s. Evaluated {len(genomes)} genomes.")
        
        # --- Report Results ---
        # Sort genomes by survival time to identify top performers
        survival_ranking = sorted([(genome_id, frames) for genome_id, frames in survival_frames.items()], 
                                 key=lambda x: x[1], reverse=True)
        
        # Get top 10% survivors for special bonus
        top_survivors_count = max(1, len(survival_ranking) // 10)
        top_survivors = set(gid for gid, _ in survival_ranking[:top_survivors_count])
        
        fitness_changes = []
        for genome_id, genome in genomes:
            # Track fitness changes for logging
            previous = previous_fitness.get(genome_id, 0.0) or 0.0
            current = fitness_values.get(genome_id, 0.0)
            fitness_change = current - previous
            fitness_changes.append((genome_id, current, fitness_change))
        
        # Log fitness stats to verify evolution is happening
        fitness_changes.sort(key=lambda x: x[1], reverse=True)
        top_10 = fitness_changes[:10]  # Only show top 10
        
        print("\n=== FITNESS REPORT ===")
        print(f"Top 10 performers:")
        for i, (gid, fit, change) in enumerate(top_10):
            change_str = f"+{change:.1f}" if change > 0 else f"{change:.1f}"
            surv_frames = survival_frames.get(gid, 0)
            print(f"  #{i+1}: Genome {gid} - Frames: {surv_frames} - Fitness: {fit:.1f} ({change_str}) - Hit")
            
        # Calculate average fitness change
        avg_change = sum(change for _, _, change in fitness_changes) / len(fitness_changes)
        print(f"Average fitness change: {avg_change:+.2f}")
        print("=====================\n")
        
    def _run_visual_simulation(self, genomes, config):
        """Run the simulation with visualization for all genomes."""
        results = []
        
        dummies_this_gen = {}  # genome_id -> Dummy instance
        networks_this_gen = {}  # genome_id -> network
        active_genomes = len(genomes)
        
        # Tracking metrics for each dummy
        survival_frames = {}  # genome_id -> frame counter
        movement_distances = {}  # genome_id -> distance moved
        head_stability = {}  # genome_id -> head stability score
        
        # Create dummies and networks for this generation
        for genome_id, genome in genomes:
            genome.fitness = 0  # Initialize fitness
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            dummy_start_pos = (DEFAULT_DUMMY_START_POS[0], 
                               DEFAULT_DUMMY_START_POS[1] + random.uniform(-20, 20))
            dummy = Dummy(self.space, dummy_start_pos, collision_type=COLLISION_TYPE_DUMMY)
            
            networks_this_gen[genome_id] = net
            dummies_this_gen[genome_id] = dummy
            survival_frames[genome_id] = 0  # Initialize frame counter
            movement_distances[genome_id] = 0.0  # Initialize movement distance
            head_stability[genome_id] = 0.0  # Initialize head stability score
        
        # Simulation loop
        while active_genomes > 0:
            # Check for visualization exit requests
            if not self.viz.running:
                print("Visualizer closed, ending generation early.")
                break
            
            # Update NNs and step physics
            current_active = 0
            for genome_id, genome in genomes:
                dummy = dummies_this_gen.get(genome_id)
                if dummy and not dummy.is_hit:
                    current_active += 1
                    # Increment frame counter
                    survival_frames[genome_id] += 1
                    
                    # Calculate movement distance
                    current_pos = dummy.get_body_position()
                    distance_moved = abs(current_pos.x - dummy.initial_position.x)
                    movement_distances[genome_id] = max(movement_distances[genome_id], distance_moved)
                    
                    # Calculate head stability
                    if hasattr(dummy, 'head'):
                        head_angle = abs(dummy.head.angle % (2 * math.pi))
                        stability_score = 1.0 - min(1.0, head_angle / math.pi)
                        head_stability[genome_id] += stability_score
                    
                    # Update neural network
                    try:
                        net = networks_this_gen[genome_id]
                        sensor_values = dummy.get_sensor_data()
                        motor_outputs = net.activate(sensor_values)
                        dummy.set_motor_rates(motor_outputs)
                    except Exception as e:
                        print(f"Error activating network for genome {genome_id}: {e}")
                        hit_pos = dummy.mark_as_hit()
                        if hit_pos:
                            self._create_explosion(hit_pos)
                        dummy.remove_from_space()
            
            # Update active count
            active_genomes = current_active
            
            # Step physics
            self.space.step(SIM_DT)
            
            # Cleanup debris
            self._cleanup_debris()
            
            # Update visualization
            self.viz.draw(self)
        
        # Prepare results in the same format as parallel simulation
        for genome_id in dummies_this_gen:
            frames = survival_frames.get(genome_id, 0)
            distance = movement_distances.get(genome_id, 0.0)
            stability = head_stability.get(genome_id, 0.0)
            fitness = float(frames)  # Fitness is just the frame count
            results.append((genome_id, fitness, frames, distance, stability))
        
        return results

    def _simulate_dummy(self, genome_config):
        """Run simulation for a single dummy in isolation.
        
        Args:
            genome_config: Tuple of (genome_id, genome, config)
            
        Returns:
            Tuple of (genome_id, fitness, frames, distance, stability)
        """
        genome_id, genome, config = genome_config
        
        # Create a separate simulation space for this dummy
        local_space = pymunk.Space()
        local_space.gravity = (0, -981.0)  # Same gravity as main simulation
        
        # Add ground
        ground = pymunk.Segment(local_space.static_body, (-5000, 10), (5000, 10), 5)
        ground.friction = 0.8
        ground.elasticity = 0.5
        ground.collision_type = COLLISION_TYPE_GROUND
        ground.filter = pymunk.ShapeFilter(categories=0b100, mask=0b001)
        local_space.add(ground)
        
        # Add laser
        laser_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        laser_body.position = (LASER_START_X, LASER_HEIGHT / 2)
        laser_body.velocity = (LASER_SPEED, 0)
        laser_shape = pymunk.Poly.create_box(laser_body, (LASER_WIDTH, LASER_HEIGHT))
        laser_shape.sensor = True
        laser_shape.collision_type = COLLISION_TYPE_LASER
        laser_shape.color = (255, 0, 0, 255)
        laser_shape.filter = pymunk.ShapeFilter(categories=0b1000, mask=0b001)
        local_space.add(laser_body, laser_shape)
        
        # Setup collision handlers
        def _local_laser_hit_dummy(arbiter, space, data):
            for shape in arbiter.shapes:
                if shape.collision_type == COLLISION_TYPE_DUMMY:
                    dummy_shape = shape
                    if hasattr(dummy_shape, 'user_data') and isinstance(dummy_shape.user_data, Dummy):
                        dummy_shape.user_data.mark_as_hit()
                        return True
            return True
            
        def _local_head_ground_collision(arbiter, space, data):
            for shape in arbiter.shapes:
                if shape.collision_type == COLLISION_TYPE_DUMMY:
                    dummy_shape = shape
                    if hasattr(dummy_shape, 'user_data') and isinstance(dummy_shape.user_data, Dummy):
                        dummy = dummy_shape.user_data
                        if dummy_shape.body == dummy.head:
                            dummy.mark_as_hit()
                            return True
            return True
            
        handler = local_space.add_collision_handler(COLLISION_TYPE_LASER, COLLISION_TYPE_DUMMY)
        handler.begin = _local_laser_hit_dummy
        
        ground_handler = local_space.add_collision_handler(COLLISION_TYPE_GROUND, COLLISION_TYPE_DUMMY)
        ground_handler.begin = _local_head_ground_collision
        
        # Create dummy
        dummy_start_pos = (DEFAULT_DUMMY_START_POS[0], 
                          DEFAULT_DUMMY_START_POS[1] + random.uniform(-20, 20))
        dummy = Dummy(local_space, dummy_start_pos, collision_type=COLLISION_TYPE_DUMMY)
        
        # Create neural network
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        
        # Simulation variables
        survival_frames = 0
        movement_distance = 0.0
        head_stability = 0.0
        max_frames = 2000  # Safety limit to prevent infinite loops
        
        # Simulation loop
        while not dummy.is_hit and survival_frames < max_frames:
            # Get sensor data and activate network
            sensor_values = dummy.get_sensor_data()
            motor_outputs = net.activate(sensor_values)
            dummy.set_motor_rates(motor_outputs)
            
            # Step physics
            local_space.step(SIM_DT)
            
            # Update metrics
            survival_frames += 1
            
            # Calculate movement distance
            current_pos = dummy.get_body_position()
            movement_distance = max(movement_distance, abs(current_pos.x - dummy.initial_position.x))
            
            # Calculate head stability
            if hasattr(dummy, 'head'):
                head_angle = abs(dummy.head.angle % (2 * math.pi))
                stability_score = 1.0 - min(1.0, head_angle / math.pi)
                head_stability += stability_score
            
            # Check if laser has passed the dummy
            if laser_body.position.x > current_pos.x + 100:
                # Dummy has survived the laser
                break
        
        # Calculate fitness (frames survived)
        fitness = float(survival_frames)
        
        # Clean up
        for shape in list(local_space.shapes):
            if shape.body:
                local_space.remove(shape)
            
        for body in list(local_space.bodies):
            if body != local_space.static_body:
                local_space.remove(body)
        
        return genome_id, fitness, survival_frames, movement_distance, head_stability
        
    def _update_visualization(self, genome_id, genome, config):
        """Run a single dummy in the main simulation for visualization."""
        if not self.viz or not self.viz.running:
            return
            
        # Create a dummy for visualization
        dummy_start_pos = (DEFAULT_DUMMY_START_POS[0], DEFAULT_DUMMY_START_POS[1])
        dummy = Dummy(self.space, dummy_start_pos, collision_type=COLLISION_TYPE_DUMMY)
        
        # Create neural network
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        
        # Visualization loop
        frames = 0
        max_frames = 500  # Limit for visualization
        
        while not dummy.is_hit and frames < max_frames and self.viz.running:
            # Get sensor data and activate network
            sensor_values = dummy.get_sensor_data()
            motor_outputs = net.activate(sensor_values)
            dummy.set_motor_rates(motor_outputs)
            
            # Step physics
            self.space.step(SIM_DT)
            
            # Update visualization
            self.viz.draw(self)
            
            frames += 1
            
        # Clean up
        dummy.remove_from_space()
        self._clear_simulation_state()
    
    # --- Removed Methods --- 
    # reset() method is removed - restarting logic now in main.py if needed
    # get_fitness() method is removed - fitness calculation would be per-dummy
    #                           and depends on the specific evolutionary goal. 