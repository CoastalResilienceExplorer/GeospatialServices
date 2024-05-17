from rio_tiler.io import Reader
from rio_tiler.mosaic.reader import mosaic_reader
import xarray as xr
import rioxarray as rxr
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from rio_tiler.profiles import img_profiles
from rio_tiler.colormap import cmap
from rio_tiler.utils import render
import logging
import uvicorn
import os, math
import numpy as np
log = logging.Logger('log')
log.setLevel(logging.INFO)

from google.cloud import storage

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

GCS_BASE=os.environ['BUCKET']

DATASETS = ["elevations/ncei19_n36x75_w121x75_2023v1.tif",
"elevations/ncei19_n36x75_w122x00_2023v1.tif",
"elevations/ncei19_n36x75_w122x25_2023v1.tif",
"elevations/ncei19_n36x75_w122x50_2023v1.tif",
"elevations/ncei19_n37x00_w121x75_2023v1.tif",
"elevations/ncei19_n37x00_w122x00_2023v1.tif",
"elevations/ncei19_n37x00_w122x25_2023v1.tif",
"elevations/ncei19_n37x00_w122x50_2023v1.tif",
"elevations/ncei19_n37x25_w121x75_2023v1.tif",
"elevations/ncei19_n37x25_w122x00_2023v1.tif",
"elevations/ncei19_n37x25_w122x25_2023v1.tif",
"elevations/ncei19_n37x25_w122x50_2023v1.tif",
"elevations/ncei19_n37x50_w122x00_2022v1.tif",
"elevations/ncei19_n37x50_w122x25_2022v1.tif",
"elevations/ncei19_n37x50_w122x50_2022v1.tif",
"elevations/ncei19_n37x50_w122x75_2022v1.tif",
"elevations/ncei19_n37x75_w122x00_2022v1.tif",
"elevations/ncei19_n37x75_w122x25_2022v1.tif",
"elevations/ncei19_n37x75_w122x50_2022v1.tif",
"elevations/ncei19_n37x75_w122x75_2022v1.tif",
"elevations/ncei19_n38x00_w122x00_2022v1.tif",
"elevations/ncei19_n38x00_w122x25_2022v1.tif",
"elevations/ncei19_n38x00_w122x50_2022v1.tif",
"elevations/ncei19_n38x00_w122x75_2022v1.tif",
"elevations/ncei19_n38x25_w122x00_2022v1.tif",
"elevations/ncei19_n38x25_w122x25_2022v1.tif",
"elevations/ncei19_n38x25_w122x50_2022v1.tif",
"elevations/ncei19_n38x25_w122x75_2022v1.tif"]

def to_rgb(data, nodata):
    '''Converts greyscale to RGB for Mapbox Terrain consumption'''

    def nodata_to_zero(data, nodata):
        return 1-(data==nodata)
    
    offset = 10000
    scale = 0.1
    
    # Data Prep
    data = (data + offset) / scale
    data = data * nodata_to_zero(data, nodata)
    
    # RGB png band creation
    r = np.floor(data / math.pow(256,2)) % 256
    g = np.floor(data / 256) % 256
    b = np.floor(data) % 256
    return np.array([r,g,b]).astype('uint8')


@app.get(
    r"/{z}/{x}/{y}.png",
    responses={
        200: {
            "content": {"image/png": {}}, "description": "Return an image.",
        }
    },
    response_class=Response,
    description="Read COG and return a tile",
)
def tile(
    z: int,
    x: int,
    y: int,
    dataset: str,
    color: str = 'ylorrd',
    min_val: int = 0,
    max_val: int = 10000,
    unscale: bool = True
):
    """Handle tile requests."""
    dataset = f'{GCS_BASE}/{dataset}'
    cm = cmap.get(color)
    options={"unscale":unscale}
    with Reader(dataset, options=options) as cog:
        img = cog.tile(x, y, z)
    img.rescale(
        in_range=((min_val, max_val),),
        out_range=((0, 255),)
    )
    content = img.render(img_format="PNG", colormap=cm, **img_profiles.get("png"))
    # print(img.data)
    # return 200
    return Response(content, media_type="image/png")


@app.get("/get_rgb_tile/{z}/{x}/{y}.png")
def get_rgb_tile(
    z:int, 
    x:int, 
    y:int, 
    dataset: str,
    unscale: bool = True
    ):
    '''Returns a Mapbox-ready elevation tile'''
    options = img_profiles.get('png')
    dataset = f'{GCS_BASE}/{dataset}'
    print(options)
    # options={"unscale":unscale}
    with Reader(dataset, options={"unscale":unscale}) as cog:
        t = cog.tile(x, y, z, tilesize=512, resampling_method='cubic')
        buff = render(
            to_rgb(t.data[0], cog.info().nodata_value),
            t.mask,  # We use dataset mask for rendering
            img_format="PNG",
            **options,
        )
        return Response(content=buff, media_type="ïmage/png")
    

def tiler(asset, *args, **kwargs):
    with Reader(asset) as src:
        return src.tile(*args, **kwargs)

@app.get("/get_rgb_tile/elevation/{z}/{x}/{y}.png")
def get_rgb_tile(
    z:int, 
    x:int, 
    y:int, 
    unscale: bool = True
    ):
    '''Returns a Mapbox-ready elevation tile'''
    options = img_profiles.get('png')
    
    # options={"unscale":unscale}
    t = mosaic_reader([f'{GCS_BASE}/{d}' for d in DATASETS], tiler, x, y, z)
    buff = render(
        to_rgb(t.data[0], 0),
        t.mask,  # We use dataset mask for rendering
        img_format="PNG",
        **options,
    )
    return Response(content=buff, media_type="ïmage/png")


@app.get('/')
def test():
    return 'OK'

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 
# x = xr.open_dataset(ghsl)
# x.band_data.isel(band=0).chunk(1000).to_zarr("GHSL_COG.zarr")
# x.band_data.isel(band=0).chunk(100).rio.to_raster("GHSL_COG.tif", driver="COG")
