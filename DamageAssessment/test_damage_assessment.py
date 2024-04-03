from damage_assessment import main as damage_assessment
from population_assessment import main as population_assessment
import subprocess
import rioxarray as rxr
import uuid

BELIZE = "./data/belize_test_flooding.tiff"


def test_damages():
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
    ds.rio.to_raster('./test1.tiff')
    population_assessment(ds, 0.5)

test_population()