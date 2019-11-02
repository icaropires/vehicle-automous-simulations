#!/usr/bin/env python

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

# Interval between pictures taken by the camera
CAMERA_INTERVAL = 0.3


if __name__ == '__main__':
    actor_list = []

    try:
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        world = client.get_world()
        blueprint_library = world.get_blueprint_library()

        vehicle_bp = random.choice(blueprint_library.filter('vehicle.tesla.*'))

        transform = random.choice(world.get_map().get_spawn_points())
        vehicle = world.spawn_actor(vehicle_bp, transform)

        coordinates_params = (
            'velocity', 'acceleration', 'angular_velocity', 'location'
        )
        rotation_params = ('pitch', 'yaw', 'roll')

        labels = [f'{attr}_{c}' for attr in coordinates_params
                  for c in ('x', 'y', 'z')]
        labels.extend(f'rotation_{attr}' for attr in rotation_params)


        control_params = ('throttle', 'steer', 'brake', 'hand_brake',
                          'reverse', 'manual_gear_shift', 'gear')
        labels.extend(f'control_{attr}' for attr in control_params)

        print(*labels, sep=',')
        def print_info(_):
            # print('Transform', vehicle.get_transform())
            coordinates_attrs = (
                getattr(vehicle, 'get_' + p)() for p in coordinates_params
            )
            values = [
                getattr(attr, c) for attr in coordinates_attrs
                for c in ('x', 'y', 'z')
            ]

            rotation = vehicle.get_transform().rotation
            values.extend(
                getattr(rotation, attr) for attr in rotation_params
            )

            control = vehicle.get_control()
            values.extend(
                getattr(control, attr) for attr in control_params
            )

            print(*values, sep=',')

        ticks = []
        ticks.append(
            world.on_tick(print_info)
        )

        for _ in range(1):
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
        for tick in ticks:
            world.remove_on_tick(tick)
        print('done.')
