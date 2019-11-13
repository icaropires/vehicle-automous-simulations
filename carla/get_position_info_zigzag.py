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

ROTATION_PARAMS = ('pitch', 'yaw', 'roll')
COORDINATES_PARAMS = ('velocity', 'acceleration',
                      'angular_velocity', 'location')
CONTROL_PARAMS = ('throttle', 'steer', 'brake', 'hand_brake',
                  'reverse', 'manual_gear_shift', 'gear')

GNSS_PARAMS = ('latitude', 'longitude', 'altitude')


if __name__ == '__main__':
    ticks = []
    actor_list = []

    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        world = client.get_world()
        blueprint_library = world.get_blueprint_library()

        vehicle_bp = random.choice(blueprint_library.filter('vehicle.tesla.*'))

        transform = random.choice(world.get_map().get_spawn_points())
        vehicle = world.spawn_actor(vehicle_bp, transform)

        gnss_bp = blueprint_library.find('sensor.other.gnss')
        gnss_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        gnss = world.spawn_actor(
            gnss_bp,
            gnss_transform,
            attach_to=vehicle
        )
        actor_list.append(gnss)

        pos_file = open('pos.csv', 'w')
        gnss_file = open('gnss.csv', 'w')

        def print_pos_labels():
            labels = ['timestamp']
            labels.extend(f'{attr}_{c}' for attr in COORDINATES_PARAMS
                          for c in ('x', 'y', 'z'))

            labels.extend(f'rotation_{attr}' for attr in ROTATION_PARAMS)

            labels.extend(f'control_{attr}' for attr in CONTROL_PARAMS)

            # print(*labels, sep=',')
            pos_file.write(','.join(map(str, labels)) + '\n')

        def print_pos_info(w_snapshot):
            coordinates_attrs = (
                getattr(vehicle, 'get_' + p)() for p in COORDINATES_PARAMS
            )

            values = [w_snapshot.platform_timestamp]
            values.extend(
                getattr(attr, c) for attr in coordinates_attrs
                for c in ('x', 'y', 'z')
            )

            rotation = vehicle.get_transform().rotation
            values.extend(
                getattr(rotation, attr) for attr in ROTATION_PARAMS
            )

            control = vehicle.get_control()
            values.extend(
                getattr(control, attr) for attr in CONTROL_PARAMS
            )

            # print(*values, sep=',')
            pos_file.write(','.join(map(str, values)) + '\n')

        def print_gnss_labels():
            labels = ['timestamp']
            labels.extend(attr for attr in GNSS_PARAMS)

            # print(*labels, sep=',')
            gnss_file.write(','.join(map(str, labels)) + '\n')

        def print_gnss_info(data):
            values = [world.get_snapshot().platform_timestamp]

            values.extend(
                getattr(data, attr) for attr in GNSS_PARAMS
            )

            # print(*values, sep=',')
            gnss_file.write(','.join(map(str, values)) + '\n')

        print('Writting gnss data...')
        print_gnss_labels()
        gnss.listen(print_gnss_info)

        print('Writting position data...')
        print_pos_labels()
        ticks.append(
            world.on_tick(print_pos_info)
        )

        # Zigzag
        for _ in range(20):
            vehicle.apply_control(
                carla.VehicleControl(throttle=1.0, steer=0.1)
            )
            time.sleep(0.5)

            vehicle.apply_control(
                carla.VehicleControl(throttle=1.0, steer=-0.1)
            )
            time.sleep(0.5)

    finally:
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()

        print('destroying ticks')
        for tick in ticks:
            world.remove_on_tick(tick)

        time.sleep(0.5)
        pos_file.close()
        gnss_file.close()

        print('done.')
