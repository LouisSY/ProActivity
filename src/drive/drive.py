# file: scripts/carla_wasd_console_controller_win.py
"""
Windows console WASD controller for CARLA 0.10.0 (hold-to-drive, release-to-stop).

Controls (hold keys):
  W / S     : forward / reverse
  A / D     : steer left / right
  SHIFT     : boost while held (with W or S)
  SPACE     : brake while held
  R         : reset to nearest spawn point
  Q or ESC  : quit

Notes:
- Uses CARLA simulator window only. Single controller, no HUD.
- Fixed vehicle: 'vehicle.dodge.charger_2020'. Map: "default" or "Mine_01".
- Driver-seat view. To reduce view "shaking" when starting to move, this script:
  (1) enables synchronous mode, and (2) smooths the spectator camera slightly.
"""

import os
import sys
import time
import math
import ctypes

try:
    import carla
except ImportError:
    print("[ERROR] Cannot import CARLA. Put the PythonAPI egg in PYTHONPATH.")
    sys.exit(1)

# --------------
# Configuration
# --------------
MAP_SELECTION = "default"   # "default" or "Mine_01"
BASE_THROTTLE = 0.40         # overall speed feel
BOOST_MULTIPLIER = 1.8       # SHIFT boost
STEER_STEP = 0.04            # steering change per tick when holding A/D
STEER_DECAY = 0.15           # recentering when no steering key is held
TARGET_FPS = 30              # control loop pacing

# Camera: driver seat offset (vehicle local: x fwd, y right, z up)
DRIVER_OFFSET_X = 0.25
DRIVER_OFFSET_Y = -0.33
DRIVER_OFFSET_Z = 1.21
CAMERA_PITCH = -2.0

# Camera smoothing (0 = off, 1 = very slow). Keep small for responsiveness.
CAMERA_SMOOTH_POS = 0.55
CAMERA_SMOOTH_YAW = 0.85

# Use synchronous mode to avoid jitter between physics and camera updates.
ENABLE_SYNC_MODE = True

# VK codes for GetAsyncKeyState
VK_SHIFT = 0x10
VK_SPACE = 0x20
VK_ESCAPE = 0x1B

# -----------
# Utilities
# -----------

def is_windows():
    return os.name == "nt"


def key_down(vk):
    return (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000) != 0


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def load_world(client, selection):
    s = (selection or "").strip().lower()
    if s == "mine_01":
        print("[INFO] Loading map: Mine_01 ...")
        return client.load_world("Mine_01")
    else:
        world = client.get_world()
        print("[INFO] Using current map: " + world.get_map().name)
        return world


def get_spawn_points(world):
    return world.get_map().get_spawn_points()


def spawn_vehicle(world, spawn_points):
    bp_lib = world.get_blueprint_library()
    bp = bp_lib.find("vehicle.dodge.charger_2020")
    if bp is None:
        raise RuntimeError("Blueprint 'vehicle.dodge.charger_2020' not found")
    if bp.has_attribute("color"):
        bp.set_attribute("color", bp.get_attribute("color").recommended_values[0])
    if not spawn_points:
        raise RuntimeError("No spawn points available")
    vehicle = world.spawn_actor(bp, spawn_points[0])
    vehicle.set_autopilot(False)
    print("[INFO] Spawned 'vehicle.dodge.charger_2020'")

    return vehicle


def nearest_spawn_index(vehicle, spawn_points):
    vloc = vehicle.get_location()
    best_i = 0
    best_d2 = 1e30
    for i in range(len(spawn_points)):
        t = spawn_points[i]
        dx = t.location.x - vloc.x
        dy = t.location.y - vloc.y
        dz = t.location.z - vloc.z
        d2 = dx * dx + dy * dy + dz * dz
        if d2 < best_d2:
            best_d2 = d2
            best_i = i
    return best_i


def reset_to_nearest_spawn(vehicle, spawn_points):
    try:
        i = nearest_spawn_index(vehicle, spawn_points)
        target = spawn_points[i]
        vehicle.set_transform(target)
        # why: stop drift after teleport
        try:
            vehicle.set_target_velocity(carla.Vector3D(0.0, 0.0, 0.0))
            vehicle.set_target_angular_velocity(carla.Vector3D(0.0, 0.0, 0.0))
        except Exception:
            pass
        vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0, steer=0.0, reverse=False))
        print("[INFO] Reset to nearest spawn (#" + str(i) + ")")
    except Exception as e:
        print("[WARN] Reset failed: " + str(e))


# Camera smoothing state (simple floats; None means uninitialized)
CAM_SMX = None
CAM_SMY = None
CAM_SMZ = None
CAM_SMYAW = None


def update_spectator(world, vehicle):
    global CAM_SMX, CAM_SMY, CAM_SMZ, CAM_SMYAW

    sp = world.get_spectator()
    tf = vehicle.get_transform()
    loc = tf.location
    rot = tf.rotation
    yaw = rot.yaw * math.pi / 180.0
    cos_y = math.cos(yaw)
    sin_y = math.sin(yaw)

    tx = loc.x + DRIVER_OFFSET_X * cos_y - DRIVER_OFFSET_Y * sin_y
    ty = loc.y + DRIVER_OFFSET_X * sin_y + DRIVER_OFFSET_Y * cos_y
    tz = loc.z + DRIVER_OFFSET_Z
    tyaw = rot.yaw

    if CAM_SMX is None:
        CAM_SMX = tx
        CAM_SMY = ty
        CAM_SMZ = tz
        CAM_SMYAW = tyaw
    else:
        # why: small low-pass to reduce "head bob" perceived from vehicle pitch/physics
        CAM_SMX = CAM_SMX + CAMERA_SMOOTH_POS * (tx - CAM_SMX)
        CAM_SMY = CAM_SMY + CAMERA_SMOOTH_POS * (ty - CAM_SMY)
        CAM_SMZ = CAM_SMZ + CAMERA_SMOOTH_POS * (tz - CAM_SMZ)
        # yaw wrap not handled for simplicity; fine for small per-frame change
        dyaw = tyaw - CAM_SMYAW
        CAM_SMYAW = CAM_SMYAW + CAMERA_SMOOTH_YAW * dyaw

    cam_loc = carla.Location(x=CAM_SMX, y=CAM_SMY, z=CAM_SMZ)
    cam_rot = carla.Rotation(pitch=CAMERA_PITCH, yaw=CAM_SMYAW, roll=0.0)
    sp.set_transform(carla.Transform(cam_loc, cam_rot))


# -----------
# Main
# -----------

def main():
    if not is_windows():
        print("[ERROR] Windows only. This script uses GetAsyncKeyState.")
        return

    print("\n=== CARLA Console WASD Controller (hold-to-drive) ===")
    print("Controls:")
    print("  W / S     : forward / reverse")
    print("  A / D     : steer left / right")
    print("  SHIFT     : boost while held")
    print("  SPACE     : brake while held")
    print("  R         : reset to nearest spawn")
    print("  Q or ESC  : quit")
    print("Notes: Synchronous mode and camera smoothing are enabled to reduce view shake.")
    print("Map selection: " + MAP_SELECTION)

    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(5.0)

    world = load_world(client, MAP_SELECTION)
    original_settings = world.get_settings()

    if ENABLE_SYNC_MODE:
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1.0 / float(TARGET_FPS)
        world.apply_settings(settings)

    spawn_points = get_spawn_points(world)
    vehicle = None

    try:
        vehicle = spawn_vehicle(world, spawn_points)

        # init camera smoothing state at first pose
        update_spectator(world, vehicle)

        steer = 0.0
        r_prev = False

        while True:
            if key_down(VK_ESCAPE) or key_down(ord('Q')):
                break

            forward = key_down(ord('W'))
            reverse = key_down(ord('S'))
            left = key_down(ord('A'))
            right = key_down(ord('D'))
            brake = key_down(VK_SPACE)
            boost = key_down(VK_SHIFT)
            r_now = key_down(ord('R'))

            if r_now and not r_prev:
                steer = 0.0
                reset_to_nearest_spawn(vehicle, spawn_points)
            r_prev = r_now

            if left and not right:
                steer -= STEER_STEP
            elif right and not left:
                steer += STEER_STEP
            else:
                steer *= (1.0 - STEER_DECAY)
                if abs(steer) < 1e-3:
                    steer = 0.0
            steer = clamp(steer, -1.0, 1.0)

            ctrl = carla.VehicleControl()
            if brake:
                ctrl.brake = 1.0
                ctrl.throttle = 0.0
                ctrl.reverse = False
            else:
                base = 0.0
                rev = False
                if forward and not reverse:
                    base = BASE_THROTTLE
                    rev = False
                elif reverse and not forward:
                    base = BASE_THROTTLE
                    rev = True
                if boost and base > 0.0:
                    base = base * BOOST_MULTIPLIER
                ctrl.throttle = clamp(base, 0.0, 1.0)
                ctrl.reverse = rev
                ctrl.brake = 0.0

            ctrl.steer = steer
            vehicle.apply_control(ctrl)

            update_spectator(world, vehicle)

            if ENABLE_SYNC_MODE:
                world.tick()
            else:
                world.wait_for_tick()
                time.sleep(1.0 / float(TARGET_FPS))

    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    finally:
        if ENABLE_SYNC_MODE:
            try:
                world.apply_settings(original_settings)
            except Exception:
                pass
        if vehicle is not None:
            try:
                vehicle.set_autopilot(False)
            except Exception:
                pass
            try:
                vehicle.destroy()
                print("[INFO] Vehicle destroyed.")
            except Exception as e:
                print("[WARN] Could not destroy vehicle: " + str(e))
        print("[INFO] Done.")


if __name__ == "__main__":
    main()
