from utils.geo import transform_point, geojson_to_geodataframe
from utils.cache import memoize_with_persistence

import geopandas as gpd
import pandas as pd
# import s2sphere
import os


def gpd_read_parquet(path):
    data = pd.read_parquet(path)
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkb(data["geometry"]))
    return gdf


gpd.read_parquet = gpd_read_parquet


def get_covering(lower_left, upper_right):
    r = s2sphere.RegionCoverer()
    p1 = s2sphere.LatLng.from_degrees(lower_left[1], lower_left[0])
    p2 = s2sphere.LatLng.from_degrees(upper_right[1], upper_right[0])
    covering = r.get_covering(s2sphere.LatLngRect.from_point_pair(p1, p2))
    return covering


def get_relevant_partitions(covering, features):
    partition_ids = [int(i.split(".")[0]) for i in os.listdir(features)]
    buff = []
    for p in partition_ids:
        p = s2sphere.CellId(p)
        for c in covering:
            if p.contains(c) or c.contains(p) or p == c:
                buff.append(p)
    return list(set(buff))



@memoize_with_persistence("/tmp/cache.pkl")
def get_bbox_filtered_gdf(features, lower_left, upper_right) -> gpd.GeoDataFrame:
    covering = get_covering(
        [lower_left.x, lower_left.y], [upper_right.x, upper_right.y]
    )

    relevant_partitions = get_relevant_partitions(covering, features)
    print(relevant_partitions)
    buff = []
    for p in relevant_partitions:
        buff.append(gpd.read_parquet(os.path.join(features, f"{p.id()}.parquet")))
    gdf = pd.concat(buff)
    print(gdf.shape)
    gdf_filtered = gdf.cx[lower_left.x : upper_right.x, lower_left.y : upper_right.y]
    return gdf_filtered


# @memoize_with_persistence('/tmp/cache')
def get_features_unpartitioned(features_file, left, bottom, right, top, CRS):
    lower_left = transform_point(left, bottom, CRS)
    upper_right = transform_point(right, top, CRS)
    features = gpd.read_parquet(
        os.path.join(os.environ["MNT_BASE"], features_file)
    )
    print(features)
    print(lower_left, upper_right)
    features = features.cx[lower_left.x:upper_right.x, lower_left.y:upper_right.y]
    return features



