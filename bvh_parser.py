"""
Simple BVH parser for calculating MPJPE
"""
import numpy as np
import re


class BVHJoint:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.offset = np.zeros(3)
        self.channels = []
        self.channel_indices = []

    def add_child(self, child):
        self.children.append(child)


class BVHMotion:
    def __init__(self):
        self.root = None
        self.joints = []
        self.frames = 0
        self.frame_time = 0.0
        self.motion_data = None

    def get_joint_positions(self, frame_index):
        """Get world positions of all joints for a given frame"""
        if frame_index >= self.frames:
            return None

        frame_data = self.motion_data[frame_index]
        positions = []

        # Build transformation matrices for each joint
        def get_world_position(joint, parent_transform=np.eye(4)):
            # Get channel values for this joint
            transform = np.eye(4)

            # Apply offset
            transform[0:3, 3] = joint.offset

            # Apply rotations from motion data
            for i, channel in enumerate(joint.channels):
                value = frame_data[joint.channel_indices[i]]

                if channel == 'Xrotation':
                    rad = np.radians(value)
                    c, s = np.cos(rad), np.sin(rad)
                    rot = np.array([[1, 0, 0, 0],
                                   [0, c, -s, 0],
                                   [0, s, c, 0],
                                   [0, 0, 0, 1]])
                    transform = transform @ rot
                elif channel == 'Yrotation':
                    rad = np.radians(value)
                    c, s = np.cos(rad), np.sin(rad)
                    rot = np.array([[c, 0, s, 0],
                                   [0, 1, 0, 0],
                                   [-s, 0, c, 0],
                                   [0, 0, 0, 1]])
                    transform = transform @ rot
                elif channel == 'Zrotation':
                    rad = np.radians(value)
                    c, s = np.cos(rad), np.sin(rad)
                    rot = np.array([[c, -s, 0, 0],
                                   [s, c, 0, 0],
                                   [0, 0, 1, 0],
                                   [0, 0, 0, 1]])
                    transform = transform @ rot
                elif channel == 'Xposition':
                    transform[0, 3] += value
                elif channel == 'Yposition':
                    transform[1, 3] += value
                elif channel == 'Zposition':
                    transform[2, 3] += value

            # Compute world transform
            world_transform = parent_transform @ transform

            # Extract world position
            world_pos = world_transform[0:3, 3]
            positions.append(world_pos.copy())

            # Recursively process children
            for child in joint.children:
                get_world_position(child, world_transform)

        get_world_position(self.root)
        return np.array(positions)


def parse_bvh(filepath):
    """Parse a BVH file and return a BVHMotion object"""
    motion = BVHMotion()

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Parse hierarchy
    i = 0
    joint_stack = []
    channel_index = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('ROOT') or line.startswith('JOINT'):
            parts = line.split()
            joint_name = parts[1]
            joint = BVHJoint(joint_name)
            motion.joints.append(joint)

            if line.startswith('ROOT'):
                motion.root = joint

            if joint_stack:
                parent = joint_stack[-1]
                parent.add_child(joint)
                joint.parent = parent

            joint_stack.append(joint)

        elif line.startswith('OFFSET'):
            parts = line.split()
            offset = [float(parts[1]), float(parts[2]), float(parts[3])]
            joint_stack[-1].offset = np.array(offset)

        elif line.startswith('CHANNELS'):
            parts = line.split()
            num_channels = int(parts[1])
            channels = parts[2:2+num_channels]
            joint_stack[-1].channels = channels
            joint_stack[-1].channel_indices = list(range(channel_index, channel_index + num_channels))
            channel_index += num_channels

        elif line.startswith('End Site'):
            # End sites are still joints with position but no rotation
            end_joint = BVHJoint(f"{joint_stack[-1].name}_end")
            motion.joints.append(end_joint)
            parent = joint_stack[-1]
            parent.add_child(end_joint)
            end_joint.parent = parent
            joint_stack.append(end_joint)

        elif line == '}':
            if joint_stack:
                joint_stack.pop()

        elif line.startswith('MOTION'):
            break

        i += 1

    # Parse motion data
    i += 1
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('Frames:'):
            motion.frames = int(line.split()[1])
        elif line.startswith('Frame Time:'):
            motion.frame_time = float(line.split()[2])
        elif line and not line.startswith('Frames') and not line.startswith('Frame Time'):
            # Motion data starts here
            break
        i += 1

    # Read all motion data
    motion_data = []
    while i < len(lines):
        line = lines[i].strip()
        if line:
            values = [float(x) for x in line.split()]
            motion_data.append(values)
        i += 1

    motion.motion_data = np.array(motion_data)

    return motion


def calculate_mpjpe(bvh1_path, bvh2_path):
    """Calculate MPJPE between two BVH files"""
    motion1 = parse_bvh(bvh1_path)
    motion2 = parse_bvh(bvh2_path)

    # Use the shorter sequence
    num_frames = min(motion1.frames, motion2.frames)
    num_joints = min(len(motion1.joints), len(motion2.joints))

    total_error = 0.0
    frame_errors = []

    for frame in range(num_frames):
        positions1 = motion1.get_joint_positions(frame)
        positions2 = motion2.get_joint_positions(frame)

        if positions1 is None or positions2 is None:
            continue

        # Calculate mean error for this frame
        frame_error = 0.0
        for j in range(num_joints):
            distance = np.linalg.norm(positions1[j] - positions2[j])
            frame_error += distance

        frame_mean_error = frame_error / num_joints
        frame_errors.append(frame_mean_error)
        total_error += frame_mean_error

    mpjpe = total_error / len(frame_errors) if frame_errors else 0.0

    return {
        'mpjpe': mpjpe,
        'num_frames': num_frames,
        'num_joints': num_joints,
        'frame_errors': frame_errors,
        'min_error': min(frame_errors) if frame_errors else 0,
        'max_error': max(frame_errors) if frame_errors else 0,
        'duration': num_frames * motion1.frame_time
    }
