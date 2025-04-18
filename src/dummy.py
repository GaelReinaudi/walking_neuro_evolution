# Placeholder for Dummy class 

import pymunk
from pymunk.vec2d import Vec2d
import math # Needed for moment calculation

class Dummy:
    def __init__(self, space: pymunk.Space, position: tuple[float, float]):
        self.space = space
        self.initial_position = Vec2d(*position)

        # --- Properties ---
        self.bodies: list[pymunk.Body] = []
        self.shapes: list[pymunk.Shape] = []
        self.joints: list[pymunk.Constraint] = []

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

        self.l_arm = self._create_part(limb_mass, arm_size, l_arm_pos)
        l_shoulder_joint = pymunk.PivotJoint(self.body, self.l_arm, l_shoulder_anchor_body, shoulder_anchor_arm)
        l_shoulder_joint.collide_bodies = False
        self.space.add(l_shoulder_joint)
        self.joints.append(l_shoulder_joint)

        # --- Create Legs ---
        self.r_leg = self._create_part(limb_mass, leg_size, r_leg_pos)
        r_hip_joint = pymunk.PivotJoint(self.body, self.r_leg, r_hip_anchor_body, hip_anchor_leg)
        r_hip_joint.collide_bodies = False
        self.space.add(r_hip_joint)
        self.joints.append(r_hip_joint)

        self.l_leg = self._create_part(limb_mass, leg_size, l_leg_pos)
        l_hip_joint = pymunk.PivotJoint(self.body, self.l_leg, l_hip_anchor_body, hip_anchor_leg)
        l_hip_joint.collide_bodies = False
        self.space.add(l_hip_joint)
        self.joints.append(l_hip_joint)

        # Add motors later if needed


    def _create_part(self, mass: float, size: tuple[float, float], position: tuple[float, float] | Vec2d, friction: float = 0.8) -> pymunk.Body:
        """Helper function to create a rectangular body part."""
        body = pymunk.Body(mass, pymunk.moment_for_box(mass, size))
        body.position = position
        shape = pymunk.Poly.create_box(body, size)
        shape.friction = friction
        shape.filter = pymunk.ShapeFilter(group=1) # Prevent self-collision within dummy parts
        self.space.add(body, shape)
        self.bodies.append(body)
        self.shapes.append(shape)
        return body

    def get_body_position(self) -> Vec2d:
        """Returns the current position of the main body."""
        return self.body.position

    # Add methods to control motors later
    # def set_motor_rates(self, rates: list[float]): ... 