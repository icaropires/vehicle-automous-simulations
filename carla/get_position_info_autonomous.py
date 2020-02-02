#!/usr/bin/env python3.6

import glob
import os
import sys

# Importing right version of Carla client package
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time
import os

ROTATION_PARAMS = ('pitch', 'yaw', 'roll')
COORDINATES_PARAMS = ('velocity', 'acceleration',
                      'angular_velocity', 'location')
CONTROL_PARAMS = ('throttle', 'steer', 'brake', 'hand_brake',
                  'reverse', 'manual_gear_shift', 'gear')

GNSS_PARAMS = ('latitude', 'longitude', 'altitude')

IMU_PARAMS = ('compass',)
IMU_COORDINATE_PARAMS = ('accelerometer', 'gyroscope')

POS_TICK_INTERVAL = str(1/50)  # seconds


def main():
    ticks = []
    actor_list = []

    n_output = len([d for d in os.listdir() if d.startswith('out')])
    out_folder = f'out{n_output:02d}'
    os.makedirs(out_folder, exist_ok=True)

    pos_file = open(f'{out_folder}/pos.csv', 'w')
    gnss_file = open(f'{out_folder}/gnss.csv', 'w')
    imu_file = open(f'{out_folder}/imu.csv', 'w')

    client = carla.Client('localhost', 2000)
    client.set_timeout(2.0)

    world = client.get_world()
    blueprint_library = world.get_blueprint_library()

    def write_pos_labels():
        labels = ['timestamp']

        labels.extend(f'{attr}_{c}' for attr in COORDINATES_PARAMS
                      for c in ('x', 'y', 'z'))

        labels.extend(f'rotation_{attr}' for attr in ROTATION_PARAMS)

        labels.extend(f'control_{attr}' for attr in CONTROL_PARAMS)

        pos_file.write(','.join(labels) + '\n')

    def write_pos_values(w_snapshot):
        coordinates_attrs = (
            getattr(vehicle, 'get_' + p)() for p in COORDINATES_PARAMS
        )

        # Get timestamp value
        values = [w_snapshot.platform_timestamp]

        # Get COORDINATES_PARAMS values
        values.extend(
            getattr(attr, c) for attr in coordinates_attrs
            for c in ('x', 'y', 'z')
        )

        # Get ROTATION_PARAMS values
        rotation = vehicle.get_transform().rotation
        values.extend(
            getattr(rotation, attr) for attr in ROTATION_PARAMS
        )

        # Get CONTROL_PARAMS values
        control = vehicle.get_control()
        values.extend(
            getattr(control, attr) for attr in CONTROL_PARAMS
        )

        pos_file.write(','.join(map(str, values)) + '\n')

    def write_gnss_labels():
        gnss_file.write(','.join(('timestamp',) + GNSS_PARAMS) + '\n')

    def write_imu_labels():
        coordinates_attrs = tuple(
            f'{attr}_{c}' for attr in IMU_COORDINATE_PARAMS
            for c in ('x', 'y', 'z')
        )

        imu_file.write(','.join(
            ('timestamp',) + coordinates_attrs + IMU_PARAMS
        ) + '\n')

    def write_gnss_values(data):
        snapshot = world.get_snapshot()
        write_pos_values(snapshot)  # Small gambiarra

        values = [snapshot.platform_timestamp]

        values.extend(
            getattr(data, attr) for attr in GNSS_PARAMS
        )

        gnss_file.write(','.join(map(str, values)) + '\n')

    def write_imu_values(data):
        values = [world.get_snapshot().platform_timestamp]

        values.extend(
            getattr(data, attr) for attr in IMU_PARAMS
        )

        attrs = (
            getattr(data, attr) for attr in IMU_COORDINATE_PARAMS
        )
        values.extend(
            getattr(attr, c) for attr in
            attrs for c in ('x', 'y', 'z')
        )

        imu_file.write(','.join(map(str, values)) + '\n')

    def get_autonomous():
        vehicle_bp = random.choice(
            blueprint_library.filter('vehicle.tesla.*')
        )

        transform = random.choice(
            world.get_map().get_spawn_points()
        )
        vehicle = world.spawn_actor(vehicle_bp, transform)

        # Carla in 0.9.7 is throwing SIGABRT after ending when using autopilot
        vehicle.set_autopilot()

        actor_list.append(vehicle)
        return vehicle

    def get_camera(vehicle):
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        camera_bp.set_attribute('sensor_tick', '0.3')

        camera = world.spawn_actor(
            camera_bp,
            camera_transform,
            attach_to=vehicle
        )
        actor_list.append(camera)

        return camera

    def get_gnss(vehicle):
        gnss_transform = carla.Transform(carla.Location(x=0.5, z=0.5))
        gnss_bp = blueprint_library.find('sensor.other.gnss')
        gnss_bp.set_attribute('sensor_tick', POS_TICK_INTERVAL)

        gnss = world.spawn_actor(
            gnss_bp,
            gnss_transform,
            attach_to=vehicle
        )
        actor_list.append(gnss)

        return gnss

    def get_imu(vehicle):
        imu_transform = carla.Transform(carla.Location(x=0.5, z=0.5))
        imu_bp = blueprint_library.find('sensor.other.imu')
        imu_bp.set_attribute('sensor_tick', POS_TICK_INTERVAL)

        imu = world.spawn_actor(
            imu_bp,
            imu_transform,
            attach_to=vehicle
        )
        actor_list.append(imu)

        return imu

    try:
        vehicle = get_autonomous()
        spectator = world.get_spectator()

        def follow(_):
            t = vehicle.get_location()
            t.x -= 5
            t.z += 5
            spectator.set_location(t)
        ticks.append(world.on_tick(follow))

        print('Initiating writing of position data...')
        write_pos_labels()
        # Write pos labels inside gnss handle function

        # ticks.append(
        #     world.on_tick(write_pos_values)
        # )

        print('Initiating writing of gnss data...')
        gnss = get_gnss(vehicle)
        write_gnss_labels()
        gnss.listen(write_gnss_values)

        print('Initiating writing of imu data...')
        imu = get_imu(vehicle)
        write_imu_labels()
        imu.listen(write_imu_values)

        print('Initiating camera recording...')
        camera = get_camera(vehicle)
        camera.listen(lambda image: image.save_to_disk(
            f'{out_folder}/{image.frame:06d}.png'
        ))

        duration = 60*5
        print()
        for i in range(duration, 0, -1):
            print(f'Letting car drive for more {i}s...', end='\r')
            time.sleep(1)
        print()
        print('Done!', end='\n\n')

    finally:
        print('Destroying ticks...')
        for tick in ticks:
            world.remove_on_tick(tick)

        print('Destroying actors...')
        for actor in actor_list:
            if isinstance(actor, carla.libcarla.Vehicle):  # Avoid segfault
                actor.set_autopilot(False)
                continue  # Let vehicles for later (segfault)

            actor.destroy()

        time.sleep(0.5)

        # Destroy vehicles
        for actor in actor_list:
            actor.destroy()

        pos_file.close()
        gnss_file.close()
        imu_file.close()

        print('done.')


if __name__ == '__main__':
    main()
