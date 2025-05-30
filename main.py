import time
import math
import scipy.io
from simple_pid import PID
import rtde_control
import rtde_receive

# Robot Configuration
ROBOT_IP = "192.168.1.1"
rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

ACCELERATION = 0.8
SPEED = 0.3
DURATION = 10  # seconds
CONTROL_FREQUENCY = 20  # Hz
CONTROL_INTERVAL = 1.0 / CONTROL_FREQUENCY

# Starting joint positions (in radians, converted from degrees)
START_POSITION_RAD = [
    math.radians(261.15),
    math.radians(-19.99),
    math.radians(10.00),
    math.radians(0),
    math.radians(90),
    math.radians(0)
]

# Oscillation amplitudes
AMPLITUDE_J1 = math.radians(2.0)
AMPLITUDE_J2 = math.radians(3.0)  # Larger swing to simulate circle
AMPLITUDE_J3 = math.radians(3.0)
AMPLITUDE_J5 = math.radians(1.0)

# PID Controllers with limits
pid_j1 = PID(0.4, 0.01, 0.02, setpoint=0, output_limits=(-0.05, 0.05))
pid_j2 = PID(0.4, 0.01, 0.02, setpoint=0, output_limits=(-0.05, 0.05))
pid_j3 = PID(0.4, 0.01, 0.02, setpoint=0, output_limits=(-0.05, 0.05))
pid_j5 = PID(0.4, 0.01, 0.02, setpoint=0, output_limits=(-0.05, 0.05))

# Move to start
print("Moving to start position...")
rtde_c.moveJ(START_POSITION_RAD, SPEED, ACCELERATION)# Move robot to the initial positions
time.sleep(1) # Wait for the robot to reach the starting position

# Data containers to store motion, power, and TCP trace data for analysis
motion_data = []
power_data = []
tcp_trace = []

print("Starting circular-style PID-controlled motion...")
start_time = time.time()
while time.time() - start_time < DURATION:
    t = time.time() - start_time

    current_joints = rtde_r.getActualQ()
    joint_velocities = rtde_r.getActualQd()
    joint_currents = rtde_r.getActualCurrent()
    tcp_pose = rtde_r.getActualTCPPose()

    # New target joint angles (simulate circular motion)
    target_j1 = START_POSITION_RAD[0] + AMPLITUDE_J1 * math.sin(2 * math.pi * 0.2 * t)
    target_j2 = START_POSITION_RAD[1] + AMPLITUDE_J2 * math.sin(2 * math.pi * 0.5 * t)
    target_j3 = START_POSITION_RAD[2] + AMPLITUDE_J3 * math.cos(2 * math.pi * 0.5 * t)
    target_j5 = START_POSITION_RAD[4] + AMPLITUDE_J5 * math.sin(2 * math.pi * 0.7 * t)

    # PID error correction
    j1_correction = pid_j1(current_joints[0] - target_j1)
    j2_correction = pid_j2(current_joints[1] - target_j2)
    j3_correction = pid_j3(current_joints[2] - target_j3)
    j5_correction = pid_j5(current_joints[4] - target_j5)

    # Apply PID corrections to the target positions for each joint
    corrected_joints = [
        target_j1 - j1_correction,
        target_j2 - j2_correction,
        target_j3 - j3_correction,
        START_POSITION_RAD[3],
        target_j5 - j5_correction,
        START_POSITION_RAD[5]
    ]

    # Command the robot
    rtde_c.servoJ(corrected_joints, SPEED, ACCELERATION, CONTROL_INTERVAL, 0.05, 300)

    # Log data
    timestamp = time.time() - start_time
    motion_data.append([timestamp] + current_joints + joint_velocities + tcp_pose)
    power_data.append([timestamp] + joint_currents)
    tcp_trace.append([timestamp] + tcp_pose)

    time.sleep(CONTROL_INTERVAL)

# Finish
print("Returning to start position...")
rtde_c.moveJ(START_POSITION_RAD, SPEED, ACCELERATION)
rtde_c.stopScript()

# Save logs
scipy.io.savemat("circular_motion_data.mat", {"motion_data": motion_data})
scipy.io.savemat("circular_power_data.mat", {"power_data": power_data})
scipy.io.savemat("circular_tcp_trace.mat", {"tcp_trace": tcp_trace})
print("Data saved successfully.")
