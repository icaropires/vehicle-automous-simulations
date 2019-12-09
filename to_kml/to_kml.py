#!/bin/env python3

import sys
import csv

import simplekml 

if len(sys.argv) < 1:
    print('Wrong usage: Usage ex: ./to_kml.py file.csv', file=sys.stderr)
    sys.exit(1)

fd = sys.argv[1]
with open(fd) as csv_file:
    csv_file = csv.reader(csv_file);

    header = next(csv_file)
    lat_idx, *_ = [i for i, l in enumerate(header) if l.startswith('lat')]
    long_idx, *_ = [i for i, l in enumerate(header) if l.startswith('long')]

    kml = simplekml.Kml(name="CARLA travel", open=1)

    linestring = kml.newlinestring(
        name="travelled",
        description="Route travelled by the autonomous vehicle"
    )

    coords = [(c[long_idx], c[lat_idx]) for c in csv_file]
    linestring.coords = coords
    print("@", coords[0])

    linestring.extrude = 1
    linestring.style.linestyle.color = 'aa00ff00' # Channels: ABGR
    linestring.style.linestyle.width= 10

    kml.save('output.kml')
