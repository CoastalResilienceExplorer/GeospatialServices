import pyproj
from shapely.geometry import Point
from shapely.ops import transform

def transform_point(x, y, crs):
    pt = Point(x, y)

    init_crs = pyproj.CRS(crs)
    wgs84 = pyproj.CRS('EPSG:4326')

    project = pyproj.Transformer.from_crs(init_crs, wgs84, always_xy=True).transform
    return transform(project, pt)