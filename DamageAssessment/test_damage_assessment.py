from damage_assessment import main as damage_assessment
from population_assessment import main as population_assessment
import subprocess
import rioxarray as rxr
import uuid
import os

BELIZE = "./data/belize_test_flooding.tiff"
WRITE = int(os.getenv('TEST_WRITE', 0))


def test_damages_no_filters():
    # This is intermediate processing to deal with non-rectilinear grids
    tmp_cog = f'/tmp/{str(uuid.uuid4())}.tiff'
    bashCommand = f"gdalwarp {BELIZE} {tmp_cog} -of COG"
    process = subprocess.Popen(bashCommand.split(' '), stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    ds = rxr.open_rasterio(tmp_cog).isel(band=0)
    damages = damage_assessment(ds)
    if WRITE:
        damages.rio.to_raster('test_damages_no_filters.tiff')

def test_population():
    import uuid
    # This is intermediate processing to deal with non-rectilinear grids
    tmp_cog = f'/tmp/{str(uuid.uuid4())}.tiff'
    bashCommand = f"gdalwarp {BELIZE} {tmp_cog} -of COG"
    process = subprocess.Popen(bashCommand.split(' '), stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    ds = rxr.open_rasterio(tmp_cog).isel(band=0)
    pop = population_assessment(ds, 0.5)
    if WRITE:
        pop.rio.to_raster('test_population.tiff')

def test_damages_with_filter():
    import uuid
    # This is intermediate processing to deal with non-rectilinear grids
    tmp_cog = f'/tmp/{str(uuid.uuid4())}.tiff'
    bashCommand = f"gdalwarp {BELIZE} {tmp_cog} -of COG"
    process = subprocess.Popen(bashCommand.split(' '), stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline()
        if not line: break
        print(line, flush=True)
    ds = rxr.open_rasterio(tmp_cog).isel(band=0)
    x = damage_assessment(ds, 100, 10)
    if WRITE:
        x.rio.to_raster('./test_damages_with_filters.tiff')

test_damages_no_filters()
test_population()
test_damages_with_filter()