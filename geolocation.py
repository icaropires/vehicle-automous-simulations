# Based on CARLA implementation

# Coordinate system: mercator = Pseudo-Mercator EPSG:3857
# Checked on: https://epsg.io/transform#s_srs=4326&t_srs=3857

import numpy as np
from collections import namedtuple

from typing import Optional

Location = namedtuple('Location', 'x y z')
GeoLocation = namedtuple('GeoLocation', 'lat lon alt')

EARTH_RADIUS_EQUA = 6378137


def lat_to_scale(lat):
    return np.cos(np.radians(lat))


def geopoint_to_mercator(lat, lon, scale):
    x = scale * np.radians(lon) * EARTH_RADIUS_EQUA
    y = scale * EARTH_RADIUS_EQUA * np.log(np.tan((90 + lat) * np.pi / 360))

    return x, y


def mercator_to_geopoint(x, y, scale):
    lon = x * 180 / (np.pi * EARTH_RADIUS_EQUA * scale)

    exp = np.exp(y / (EARTH_RADIUS_EQUA * scale))
    lat = 360 * np.arctan(exp) / np.pi - 90

    return lat, lon


def geopoint_add_meters(dx, dy, reference):
    scale = lat_to_scale(reference.lat)

    mx, my = geopoint_to_mercator(reference.lat, reference.lon, scale)

    mx += dx
    my += dy

    mx, my = mercator_to_geopoint(mx, my, scale)
    return GeoLocation(mx, my, reference.alt + location.z)


def to_geolocation(
    location: Location,
    reference: Optional[GeoLocation] = None
) -> GeoLocation:

    reference = reference or GeoLocation(0, 0, 0)
    return geopoint_add_meters(location.x, -location.y, reference)


if __name__ == '__main__':
    x, y, z = map(float, input().split())

    location = Location(x, y, z)
    reference = GeoLocation(49, 8, 0)  # Default on CARLA simulator

    print(to_geolocation(location, reference))
