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


if __name__ == '__main__':
    # List for keeping record of all actors spawned to the world
    # so they can be destroyed them when this script are finished
    actor_list = []

    try:
        # Declaring the client and setting timeout for connecting
        # with the server
        client = carla.Client('localhost', 2000)
        # Just for not trying to connect forever if server
        # is not reacheable
        client.set_timeout(2.0)

        # Connect with the server and get a 'world' reference
        world = client.get_world()

        # Almost all things in Carla world are blueprints,
        # this is how to get it
        blueprint_library = world.get_blueprint_library()

        # Get a Tesla vehicle from the blueprint library
        vehicle_bp = random.choice(
            blueprint_library.filter('vehicle.tesla.*')
        )

        # Get a random possible (no conflicts) position to spawn
        # the vehicle and spawn it
        transform = random.choice(
            world.get_map().get_spawn_points()
        )
        vehicle = world.spawn_actor(vehicle_bp, transform)

        actor_list.append(vehicle)  # Register vehicle actor
        print(f'created {vehicle.type_id}')

        # Let's get a RGB camera and set some attributes
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        # Coordinates are given relative to the vehicle in meters
        camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        # Image size in pixels
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        # Interval between pictures in seconds
        camera_bp.set_attribute('sensor_tick', '0.3')

        # Spawn the camera and attach it to the vehicle
        camera = world.spawn_actor(
            camera_bp,
            camera_transform,
            attach_to=vehicle
        )
        actor_list.append(camera)  # Register the camera actor
        print(f'created {camera.type_id}')

        # Let's also add a GNSS sensor
        gnss_bp = blueprint_library.find('sensor.other.gnss')
        # Coordinates are given relative to the vehicle in meters
        gnss_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
        gnss = world.spawn_actor(
            gnss_bp,
            gnss_transform,
            attach_to=vehicle
        )
        actor_list.append(gnss)  # Register the gnss actor
        print(f'created {gnss.type_id}')

        # Check how much "out" folders already exists, to use as index
        n_output = len([d for d in os.listdir() if d.startswith('out')])

        # Sets the function that will be called by the camera
        # It'll save the images to disk at a "out" folder
        camera.listen(lambda image: image.save_to_disk(
            f'out{n_output:02d}/{image.frame:06d}.png'
        ))

        # Sets the function that will be called by the GNSS
        # It'll print the parameters to the terminal
        gnss.listen(
            lambda data: print(
                f'timestamp {data.timestamp:0.3f},'
                f' latitude {data.latitude:0.3f},'
                f' longitude {data.longitude:0.3f},'
                f' altitude {data.altitude:0.3f}'
            )
        )

        # Driving right and left some times
        for _ in range(20):
            # Accelerates and go right
            vehicle.apply_control(
                carla.VehicleControl(throttle=1.0, steer=0.1)
            )
            time.sleep(0.5)  # Let it go

            # Accelerates and go left
            vehicle.apply_control(
                carla.VehicleControl(throttle=1.0, steer=-0.1)
            )
            time.sleep(0.5)  # Let it go

    finally:
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')
