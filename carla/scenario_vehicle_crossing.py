#!/usr/bin/env python3.6

# Is a work in progress
# TODO: split to multiple files

import glob
import os
import sys

import carla

import zmq
import random
import time
import os

ROTATION_PARAMS = ("pitch", "yaw", "roll")

COORDINATES_PARAMS = ("velocity", "acceleration", "angular_velocity", "location")

CONTROL_PARAMS = (
    "throttle",
    "steer",
    "brake",
    "hand_brake",
    "reverse",
    "manual_gear_shift",
    "gear",
) 
GNSS_PARAMS = ("latitude", "longitude", "altitude")

IMU_PARAMS = ("compass",)
IMU_COORDINATE_PARAMS = ("accelerometer", "gyroscope")

POS_TICK_INTERVAL = str(1 / 50)  # seconds

actor_list = []


class Factory:
    def __init__(self, world, blueprint_library):
        self.world = world
        self.blueprint_library = blueprint_library

    def get_vehicles(self):
        crossing_bp = self.blueprint_library.filter("vehicle.nissan.micra")[0]
        crossing_bp.set_attribute("color", "255,255,255")  # Vehicle that cross the street

        vehicles = {
            "ego": self.world.spawn_actor(
                self.blueprint_library.filter("vehicle.audi.etron")[0],
                carla.Transform(
                    carla.Location(x=41.5, y=262, z=1), carla.Rotation(yaw=90)
                ),
            ),
            "parked": self.world.spawn_actor(
                self.blueprint_library.filter("vehicle.nissan.patrol")[0],
                carla.Transform(
                    carla.Location(x=46.5, y=271, z=1), carla.Rotation(yaw=90)
                ),
            ),
            "crossing": self.world.spawn_actor(
                crossing_bp,
                carla.Transform(carla.Location(x=6, y=302, z=1), carla.Rotation(yaw=0)),
            ),
            "walker": self.world.spawn_actor(
                self.blueprint_library.filter("walker.pedestrian.0001")[0],
                carla.Transform(
                    carla.Location(x=37.5, y=295, z=0), carla.Rotation(yaw=90)
                ),
            ),
            "bicycle": self.world.spawn_actor(
                self.blueprint_library.filter("vehicle.bh.crossbike")[0],
                carla.Transform(
                    carla.Location(x=38.5, y=297, z=0), carla.Rotation(yaw=90)
                ),
            ),
        }

        # Remember that location origin is on the center of the vehicle
        # Bounding box extent is only half of the real extent
        # Config the position of the vehicles and VRUs
        end_of_road = 300

        ego_length = vehicles["ego"].bounding_box.extent.y * 2
        ego_location = vehicles["ego"].get_location()
        ego_location.y = end_of_road - 42 + ego_length / 2
        vehicles["ego"].set_location(ego_location)

        parked_length = vehicles["parked"].bounding_box.extent.y * 2
        parked_location = vehicles["parked"].get_location()
        parked_location.y = end_of_road - 42 + 20 + parked_length / 2
        vehicles["parked"].set_location(parked_location)

        actor_list.extend(vehicles.values())
        return vehicles

    def get_camera(self, vehicle):
        veh_location = vehicle.get_location()

        # 0 = FL, 1 = FR, 2 = BL, 3 = BR
        wheels = [w.position/100 for w in vehicle.get_physics_control().wheels]

        middle_rear_axle_x = (wheels[2].x + wheels[3].x) / 2
        middle_rear_axle_y = (wheels[2].y + wheels[3].y) / 2
        axle_to_center = ((middle_rear_axle_x-veh_location.x)**2 + (middle_rear_axle_y-veh_location.y)**2)**(1/2)
        wheel_radius = vehicle.get_physics_control().wheels[2].radius

        # Relative to vehicle location
        ground = wheels[2].z-wheel_radius/100
        location = carla.Location(
            x=3.37-axle_to_center,  # 3.37 camera position Fabio
            z=1.39-veh_location.z+ground  
        )

        rotation = carla.Rotation(roll=-0.22, pitch=-0.73, yaw=0.46)

        camera_bp = self.blueprint_library.find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", "1280")
        camera_bp.set_attribute("image_size_y", "720")
        camera_bp.set_attribute("sensor_tick", str(1/30))

        camera_transform = carla.Transform(location, rotation)  # vehicle coordinates since it is attached to the vehicle, if not attached to an actor use global coordinates and the sensor do not move anymore
        camera = self.world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

        actor_list.append(camera)

        return camera

    def get_gnss(self, vehicle):
        gnss_transform = carla.Transform(carla.Location(x=0.5, z=0.5))
        gnss_bp = self.blueprint_library.find("sensor.other.gnss")
        gnss_bp.set_attribute("sensor_tick", POS_TICK_INTERVAL)

        gnss = self.world.spawn_actor(gnss_bp, gnss_transform, attach_to=vehicle)
        actor_list.append(gnss)

        return gnss

    def get_imu(self, vehicle):
        imu_transform = carla.Transform(carla.Location(x=0.5, z=0.5))
        imu_bp = self.blueprint_library.find("sensor.other.imu")
        imu_bp.set_attribute("sensor_tick", POS_TICK_INTERVAL)

        imu = self.world.spawn_actor(imu_bp, imu_transform, attach_to=vehicle)
        actor_list.append(imu)

        return imu


def main():
    n_output = len([d for d in os.listdir() if d.startswith("out")])
    out_folder = f"out{n_output:02d}"
    os.makedirs(out_folder, exist_ok=True)

    pos_file = open(f"{out_folder}/pos.csv", "w")
    gnss_file = open(f"{out_folder}/gnss.csv", "w")
    imu_file = open(f"{out_folder}/imu.csv", "w")

    client = carla.Client("localhost", 2000)
    client.set_timeout(5.0)

    world = client.get_world()
    if world.get_map().name != "Carissma":
        client.load_world("Carissma")
        world = client.reload_world()

    blueprint_library = world.get_blueprint_library()

    spectator = world.get_spectator()
    spectator.set_transform(
        carla.Transform(
            carla.Location(x=30.8, y=274.4, z=50), carla.Rotation(pitch=-90),
        )
    )

    factory = Factory(world, blueprint_library)
    vehs = factory.get_vehicles()

    tracked_veh = vehs["ego"]

    def write_pos_labels():
        labels = ["timestamp"]

        labels.extend(
            f"{attr}_{c}" for attr in COORDINATES_PARAMS for c in ("x", "y", "z")
        )

        labels.extend(f"rotation_{attr}" for attr in ROTATION_PARAMS)

        labels.extend(f"control_{attr}" for attr in CONTROL_PARAMS)

        pos_file.write(",".join(labels) + "\n")

    def write_pos_values(w_snapshot):
        coordinates_attrs = (
            getattr(tracked_veh, "get_" + p)() for p in COORDINATES_PARAMS
        )

        # Get timestamp value
        values = [w_snapshot.platform_timestamp]

        # Get COORDINATES_PARAMS values
        values.extend(
            getattr(attr, c) for attr in coordinates_attrs for c in ("x", "y", "z")
        )

        # Get ROTATION_PARAMS values
        rotation = tracked_veh.get_transform().rotation
        values.extend(getattr(rotation, attr) for attr in ROTATION_PARAMS)

        # Get CONTROL_PARAMS values
        control = tracked_veh.get_control()
        values.extend(getattr(control, attr) for attr in CONTROL_PARAMS)

        pos_file.write(",".join(map(str, values)) + "\n")

    def write_gnss_labels():
        gnss_file.write(",".join(("timestamp",) + GNSS_PARAMS) + "\n")

    def write_imu_labels():
        coordinates_attrs = tuple(
            f"{attr}_{c}" for attr in IMU_COORDINATE_PARAMS for c in ("x", "y", "z")
        )

        imu_file.write(",".join(("timestamp",) + coordinates_attrs + IMU_PARAMS) + "\n")

    def write_gnss_values(data):
        snapshot = world.get_snapshot()
        write_pos_values(snapshot)  # Small gambiarra

        values = [snapshot.platform_timestamp]

        values.extend(getattr(data, attr) for attr in GNSS_PARAMS)

        gnss_file.write(",".join(map(str, values)) + "\n")

    def write_imu_values(data):
        values = [world.get_snapshot().platform_timestamp]

        values.extend(getattr(data, attr) for attr in IMU_PARAMS)

        attrs = (getattr(data, attr) for attr in IMU_COORDINATE_PARAMS)
        values.extend(getattr(attr, c) for attr in attrs for c in ("x", "y", "z"))

        imu_file.write(",".join(map(str, values)) + "\n")

    try:
        print("Initiating writing of position data...")
        write_pos_labels()

        print("Initiating writing of gnss data...")
        gnss = factory.get_gnss(tracked_veh)
        write_gnss_labels()
        gnss.listen(write_gnss_values)

        print("Initiating writing of imu data...")
        imu = factory.get_imu(tracked_veh)
        write_imu_labels()
        imu.listen(write_imu_values)

        print("Initiating camera recording...")
        time.sleep(1)  # Let car to to the ground
        camera = factory.get_camera(tracked_veh)
        camera.listen(
            lambda image: image.save_to_disk(f"{out_folder}/{image.frame:06d}.png")
        )

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:5555")

        print("Waiting for data...")
        while True:
            speed = socket.recv()
            tracked_veh.set_velocity(carla.Vector3D(0, float(speed), 0))
            socket.send(b'1')  # received!

    finally:
        print("Destroying actors...")
        vehicles_list = list()
        for actor in actor_list:
            if isinstance(actor, carla.libcarla.Vehicle):  # Avoid segfault
                actor.set_autopilot(False)
                vehicles_list.append(actor)
                continue  # Let vehicles for later (segfault)

            actor.destroy()

        time.sleep(0.5)

        # Destroy vehicles
        for v in vehicles_list:
            v.destroy()

        pos_file.close()
        gnss_file.close()
        imu_file.close()

        print("done.")


if __name__ == "__main__":
    main()
