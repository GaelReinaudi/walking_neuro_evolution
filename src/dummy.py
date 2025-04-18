# Placeholder for Dummy class 

import pymunk
from pymunk.vec2d import Vec2d
import math # Needed for moment calculation
import random # For default color

# Constants for motors
MOTOR_RATE = 5 # Max angular velocity (rad/s)
MOTOR_MAX_FORCE = 50000 # Max force the motor can apply
EXPLOSION_IMPULSE = 150 # Adjust this value for bigger/smaller explosions

class Dummy:
    _next_id = 0 # Class variable for assigning unique IDs

    def __init__(self, space: pymunk.Space, position: tuple[float, float], collision_type: int):
        """Initializes the dummy with body parts, joints, motors, assigns collision types, colors, and an ID."""
        self.space = space
        self.initial_position = Vec2d(*position)
        self.collision_type = collision_type
        self.id = Dummy._next_id
        Dummy._next_id += 1

        # --- Properties ---
        self.bodies: list[pymunk.Body] = []
        self.shapes: list[pymunk.Shape] = []
        self.joints: list[pymunk.Constraint] = []
        self.motors: list[pymunk.SimpleMotor] = []
        self.is_hit = False # Flag to indicate if hit by laser
        self.hit_color = (255, 0, 0, 255) # Red
        self.default_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200), 255)
        # Sensor placeholders (update these properly later)
        self.r_foot_contact = False
        self.l_foot_contact = False
        self.final_x: float | None = None # Store final X position when hit

        # --- Define body part dimensions and masses ---
        body_mass = 10
        body_size = (30, 40) # Make body slightly taller
        head_mass = 2
        head_size = (20, 20)
        limb_mass = 1
        arm_size = (10, 35)
        leg_size = (10, 45)

        # --- Calculate relative positions and joint anchors ---
        body_x = self.initial_position.x
        body_y = self.initial_position.y

        head_pos = (body_x, body_y + body_size[1] / 2 + head_size[1] / 2)
        head_joint_anchor_body = (0, body_size[1] / 2)
        head_joint_anchor_head = (0, -head_size[1] / 2)

        # Arm positions (relative to body center)
        arm_y = body_y + body_size[1] / 4 # Shoulder attachment higher up
        r_arm_pos = (body_x + body_size[0] / 2 + arm_size[0] / 2, arm_y)
        l_arm_pos = (body_x - body_size[0] / 2 - arm_size[0] / 2, arm_y)
        r_shoulder_anchor_body = (body_size[0] / 2, body_size[1] / 4)
        l_shoulder_anchor_body = (-body_size[0] / 2, body_size[1] / 4)
        shoulder_anchor_arm = (0, arm_size[1] / 2) # Attach at top end of arm

        # Leg positions (relative to body center)
        leg_y = body_y - body_size[1] / 2 # Hip joint at bottom of body
        r_leg_pos = (body_x + body_size[0] / 4, leg_y - leg_size[1] / 2) # Legs closer together
        l_leg_pos = (body_x - body_size[0] / 4, leg_y - leg_size[1] / 2)
        r_hip_anchor_body = (body_size[0] / 4, -body_size[1] / 2)
        l_hip_anchor_body = (-body_size[0] / 4, -body_size[1] / 2)
        hip_anchor_leg = (0, leg_size[1] / 2) # Attach at top end of leg


        # --- Create Body ---
        self.body = self._create_part(body_mass, body_size, self.initial_position)

        # --- Create Head ---
        self.head = self._create_part(head_mass, head_size, head_pos)
        # Use anchors relative to each body's center of gravity
        head_joint = pymunk.PivotJoint(self.body, self.head, head_joint_anchor_body, head_joint_anchor_head)
        head_joint.collide_bodies = False
        self.space.add(head_joint)
        self.joints.append(head_joint)


        # --- Create Arms ---
        self.r_arm = self._create_part(limb_mass, arm_size, r_arm_pos)
        r_shoulder_joint = pymunk.PivotJoint(self.body, self.r_arm, r_shoulder_anchor_body, shoulder_anchor_arm)
        r_shoulder_joint.collide_bodies = False
        self.space.add(r_shoulder_joint)
        self.joints.append(r_shoulder_joint)
        # Add motor
        r_shoulder_motor = pymunk.SimpleMotor(self.body, self.r_arm, 0) # Start rate 0
        r_shoulder_motor.max_force = MOTOR_MAX_FORCE
        self.space.add(r_shoulder_motor)
        self.motors.append(r_shoulder_motor)

        self.l_arm = self._create_part(limb_mass, arm_size, l_arm_pos)
        l_shoulder_joint = pymunk.PivotJoint(self.body, self.l_arm, l_shoulder_anchor_body, shoulder_anchor_arm)
        l_shoulder_joint.collide_bodies = False
        self.space.add(l_shoulder_joint)
        self.joints.append(l_shoulder_joint)
        # Add motor
        l_shoulder_motor = pymunk.SimpleMotor(self.body, self.l_arm, 0)
        l_shoulder_motor.max_force = MOTOR_MAX_FORCE
        self.space.add(l_shoulder_motor)
        self.motors.append(l_shoulder_motor)

        # --- Create Legs ---
        self.r_leg = self._create_part(limb_mass, leg_size, r_leg_pos)
        r_hip_joint = pymunk.PivotJoint(self.body, self.r_leg, r_hip_anchor_body, hip_anchor_leg)
        r_hip_joint.collide_bodies = False
        self.space.add(r_hip_joint)
        self.joints.append(r_hip_joint)
        # Add motor
        r_hip_motor = pymunk.SimpleMotor(self.body, self.r_leg, 0)
        r_hip_motor.max_force = MOTOR_MAX_FORCE
        self.space.add(r_hip_motor)
        self.motors.append(r_hip_motor)

        self.l_leg = self._create_part(limb_mass, leg_size, l_leg_pos)
        l_hip_joint = pymunk.PivotJoint(self.body, self.l_leg, l_hip_anchor_body, hip_anchor_leg)
        l_hip_joint.collide_bodies = False
        self.space.add(l_hip_joint)
        self.joints.append(l_hip_joint)
        # Add motor
        l_hip_motor = pymunk.SimpleMotor(self.body, self.l_leg, 0)
        l_hip_motor.max_force = MOTOR_MAX_FORCE
        self.space.add(l_hip_motor)
        self.motors.append(l_hip_motor)

        # Add motors later if needed


    def _create_part(self, mass: float, size: tuple[float, float], position: tuple[float, float] | Vec2d, friction: float = 0.8) -> pymunk.Body:
        """Helper function to create a rectangular body part, assign collision type, user_data, and color."""
        body = pymunk.Body(mass, pymunk.moment_for_box(mass, size))
        body.position = position
        shape = pymunk.Poly.create_box(body, size)
        shape.friction = friction
        shape.filter = pymunk.ShapeFilter(group=1)
        shape.collision_type = self.collision_type
        shape.user_data = self # Store reference to this Dummy instance
        shape.color = self.default_color # Assign initial color
        self.space.add(body, shape)
        self.bodies.append(body)
        self.shapes.append(shape)
        return body

    def remove_from_space(self) -> None:
        """Removes all bodies, shapes, joints, and motors associated with this dummy from the space."""
        for motor in self.motors:
            if motor in self.space.constraints:
                self.space.remove(motor)
        for joint in self.joints:
            if joint in self.space.constraints:
                self.space.remove(joint)
        for shape in self.shapes:
            if shape in self.space.shapes:
                self.space.remove(shape)
        for body in self.bodies:
             if body in self.space.bodies:
                self.space.remove(body)
        self.motors.clear()
        self.joints.clear()
        self.shapes.clear()
        self.bodies.clear()

    def get_body_position(self) -> Vec2d:
        """Returns the current position of the main body."""
        return self.body.position

    # --- Motor Control ---
    def set_motor_rates(self, rates: list[float]) -> None:
        """Sets the target angular velocity for each motor.

        Args:
            rates: A list of desired rates (rad/s) for the motors.
                   Order should match self.motors (e.g., r_shoulder, l_shoulder, r_hip, l_hip).
                   Values typically scaled by MOTOR_RATE.
        """ 
        # Check if dummy is already hit/exploding - if so, don't apply motor commands
        if self.is_hit or not self.motors:
             return
             
        if len(rates) != len(self.motors):
            print(f"Warning: Mismatch between rates provided ({len(rates)}) and motors ({len(self.motors)}) for Dummy {self.id}")
            return

        for motor, rate_input in zip(self.motors, rates):
            motor.rate = rate_input * MOTOR_RATE

    # --- Sensor Data ---
    def get_sensor_data(self) -> list[float]:
        """Collects and returns sensor data for the neural network.

        Returns:
            A list of sensor values (e.g., relative angles, contact flags).
            Order: r_shoulder_angle, l_shoulder_angle, r_hip_angle, l_hip_angle,
                   r_foot_contact, l_foot_contact
        """
        # Return default/zero sensors if hit, as parts may be gone
        if self.is_hit:
            return [0.0] * 6 # Match expected sensor count

        sensors: list[float] = []
        body_angle = self.body.angle
        sensors.append(self.r_arm.angle - body_angle)
        sensors.append(self.l_arm.angle - body_angle)
        sensors.append(self.r_leg.angle - body_angle)
        sensors.append(self.l_leg.angle - body_angle)
        sensors.append(1.0 if self.r_foot_contact else 0.0)
        sensors.append(1.0 if self.l_foot_contact else 0.0)
        return sensors

    # --- Hit State --- 
    def mark_as_hit(self) -> Vec2d | None:
        """Marks the dummy as hit, stores final X position, and returns its current center position."""
        if not self.is_hit:
            self.is_hit = True
            self.final_x = self.body.position.x # Record final position
            print(f"Dummy {self.id} internally marked as hit at x={self.final_x:.2f}.")
            return self.body.position 
        return None # Already hit

    # Add methods to control motors later
    # def set_motor_rates(self, rates: list[float]): ... 