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


if __name__ == '__main__':
    ticks = []
    actor_list = []
    autonomous_list = []

    n_output = len([d for d in os.listdir() if d.startswith('out')])
    out_folder = f'out{n_output:02d}'
    os.makedirs(out_folder, exist_ok=True)

    pos_file = open(f'{out_folder}/pos.csv', 'w')
    gnss_file = open(f'{out_folder}/gnss.csv', 'w')

    client = carla.Client('localhost', 2000)
    client.set_timeout(2.0)

    world = client.get_world()
    blueprint_library = world.get_blueprint_library()


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

    def get_autonomous():
        vehicle_bp = random.choice(blueprint_library.filter('vehicle.tesla.*'))

        transform = random.choice(world.get_map().get_spawn_points())
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor

        batch = [
            SpawnActor(vehicle_bp, transform).then(SetAutopilot(FutureActor, True))
        ]

        for response in client.apply_batch_sync(batch):
            if not response.error:
                autonomous_list.append(response.actor_id)
            else:
                logging.error(response.error)

        vehicle_id, *_ = autonomous_list
        vehicle = world.get_actor(vehicle_id)

        return vehicle

    def get_gnss(vehicle):
        gnss_bp = blueprint_library.find('sensor.other.gnss')
        gnss_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        gnss = world.spawn_actor(
            gnss_bp,
            gnss_transform,
            attach_to=vehicle
        )
        actor_list.append(gnss)

        return gnss

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

    try:
        vehicle = get_autonomous()

        print('Initiating writting of gnss data...')
        gnss = get_gnss(vehicle)
        print_gnss_labels()
        gnss.listen(print_gnss_info)

        print('Initiating getting of position data...')
        print_pos_labels()
        ticks.append(
            world.on_tick(print_pos_info)
        )

        print('Initiating getting of position data...')
        camera = get_camera(vehicle)
        camera.listen(lambda image: image.save_to_disk(
            f'{out_folder}/{image.frame:06d}.png'
        ))

        duration = 30
        print()
        for i in range(duration, 0, -1):
            print(f'Letting car drive for more {i}s...', end='\r')
            time.sleep(1)
        print()
        print('Done!', end='\n\n')

    finally:
        print('Destroying actors...')
        for actor in actor_list:
            actor.destroy()

        print('Destroying ticks...')
        for tick in ticks:
            world.remove_on_tick(tick)

        print('Destroying autonomous...')
        client.apply_batch([carla.command.DestroyActor(x) for x in autonomous_list])

        time.sleep(0.5)
        pos_file.close()
        gnss_file.close()

        print('done.')
