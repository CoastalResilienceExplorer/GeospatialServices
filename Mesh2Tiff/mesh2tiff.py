import os
import logging
import uuid
import subprocess
import geopandas as gpd
import pandas as pd
import math
from shapely.ops import cascaded_union
from shapely import Point, Polygon
import argparse, shutil

logging.basicConfig()
logging.root.setLevel(logging.INFO)

def gdf_from_points(df, x='x', y='y'):
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[x], df[y]), crs="EPSG:4326"
    )

def buffer_points(gdf, res):
    return gpd.GeoSeries(cascaded_union(list(gdf.geometry.buffer(res))))

def run_bash_command(cmd):
    process = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)

def create_vrt(id, csv_filename, vrt_filename, x="x", y="y", z="z"):
    VRT_string = f'''
        <OGRVRTDataSource>
        <OGRVRTLayer name="{id}">
            <SrcDataSource>{csv_filename}</SrcDataSource>
            <GeometryType>wkbPoint</GeometryType>
            <GeometryField encoding="PointFromColumns" x="{x}" y="{y}" z="{z}"/>
        </OGRVRTLayer>
        </OGRVRTDataSource>
    '''
    with open(vrt_filename, 'w') as f:
        f.write(VRT_string)

def mesh2tiff(id, input_csv, resolution, crs, outpath):
    tmp_csv = f'/tmp/{id}.csv'
    tmp_vrt = f'/tmp/{id}.vrt'
    tmp_hull = f'/tmp/{id}_hull.shp'
    tmp_dem = f'/tmp/{id}.tiff'
    output_dem = os.path.join(outpath, f'{id}.tiff')
    shutil.copyfile(input_csv, tmp_csv)
    create_vrt(id, tmp_csv, tmp_vrt) 
    print("Created VRT")
    gdf = gdf_from_points(pd.read_csv(input_csv))
    tight_hull = buffer_points(gdf, 10)
    tight_hull.to_file(tmp_hull)
    left, bottom, right, top = gdf.total_bounds
    print(gdf.total_bounds)
    bashCommand = f'gdal_grid -a linear:radius=0.001:nodata=-1 -txe {math.floor(left*10000)/10000.0} {math.ceil(right*10000)/10000.0} -tye {math.floor(bottom*10000)/10000.0} {math.ceil(top*10000)/10000.0} -tr {resolution} {resolution} -of GTiff -ot Float32 -l {id} {tmp_vrt} {tmp_dem}'
    print(bashCommand)
    run_bash_command(bashCommand)

    # # Clip to Convex Hull
    clipCommand = f'gdalwarp -s_srs {crs} -of COG -cutline {tmp_hull} -cl {f"{id}_hull"} -crop_to_cutline {tmp_dem} {output_dem}'
    print(clipCommand)
    run_bash_command(clipCommand)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Mesh2Tiff", description="Converts XYZ CSVs to Tiff")
    parser.add_argument(
        'input_csv',
        type=str
    )
    parser.add_argument(
        '-r',
        '--resolution',
        type=float,
        default=5
    )
    parser.add_argument(
        '--crs',
        type=str,
        default="EPSG:4326"
    )
    args = parser.parse_args()
    id = args.input_csv.split('/')[-1].split('.')[0]
    outpath = '/data/outputs'
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    print(id, args.input_csv, args.resolution, args.crs, outpath)
    mesh2tiff(id, args.input_csv, args.resolution, args.crs, outpath)