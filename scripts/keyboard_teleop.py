#!/usr/bin/env python3
import sys
import select
import termios
import tty
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Joint limits based on SO-101 URDFs
JOINTS = {
    'shoulder_pan': {'min': -1.919, 'max': 1.919},
    'shoulder_lift': {'min': -1.745, 'max': 1.745},
    'elbow_flex': {'min': -1.690, 'max': 1.690},
    'wrist_flex': {'min': -1.658, 'max': 1.658},
    'wrist_roll': {'min': -2.743, 'max': 2.841},
    'gripper': {'min': -0.174, 'max': 1.745}
}

# Mapping keyboard keys to (joint_name, step_size_in_radians)
KEY_MAPPINGS = {
    'q': ('shoulder_pan', 0.05),
    'a': ('shoulder_pan', -0.05),
    'w': ('shoulder_lift', 0.05),
    's': ('shoulder_lift', -0.05),
    'e': ('elbow_flex', 0.05),
    'd': ('elbow_flex', -0.05),
    'r': ('wrist_flex', 0.05),
    'f': ('wrist_flex', -0.05),
    't': ('wrist_roll', 0.05),
    'g': ('wrist_roll', -0.05),
    'y': ('gripper', 0.05),
    'h': ('gripper', -0.05)
}

UI_MSG = """
SO-101 Keyboard Teleoperation
---------------------------
Moving joints:
   q/a : shoulder_pan   (+/-)
   w/s : shoulder_lift  (+/-)
   e/d : elbow_flex     (+/-)
   r/f : wrist_flex     (+/-)
   t/g : wrist_roll     (+/-)
   y/h : gripper        (+/-)

SPACE  : Reset all joints to 0
CTRL-C : Quit
"""

class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__('keyboard_teleop')
        self.publisher_ = self.create_publisher(JointState, '/leader/joint_states', 10)
        self.joint_names = list(JOINTS.keys())
        self.positions = {name: 0.0 for name in self.joint_names}

        # Publish at 50Hz to match standard teleop rate
        self.timer = self.create_timer(0.02, self.timer_callback)
        self.get_logger().info('Keyboard Teleop Node started. Awaiting input...')

    def update_joint(self, key):
        if key == ' ':
            for name in self.joint_names:
                self.positions[name] = 0.0
            return True

        if key in KEY_MAPPINGS:
            joint_name, step = KEY_MAPPINGS[key]
            new_pos = self.positions[joint_name] + step
            limits = JOINTS[joint_name]
            # Clip position to limits
            self.positions[joint_name] = max(limits['min'], min(new_pos, limits['max']))

            # Print current status nicely
            sys.stdout.write('\r\033[K') # Clear line
            status = " | ".join([f"{name[:3]}:{self.positions[name]:+.2f}" for name in self.joint_names])
            sys.stdout.write(status)
            sys.stdout.flush()

            return True
        return False

    def timer_callback(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [self.positions[name] for name in self.joint_names]
        self.publisher_.publish(msg)

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    # Non-blocking read
    rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
    key = sys.stdin.read(1) if rlist else ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main(args=None):
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init(args=args)
    node = KeyboardTeleop()

    print(UI_MSG)

    try:
        while rclpy.ok():
            key = get_key(settings)
            if key == '\x03': # CTRL-C
                print("\nQuitting...")
                break
            if key:
                node.update_joint(key)

            rclpy.spin_once(node, timeout_sec=0)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

if __name__ == '__main__':
    main()
