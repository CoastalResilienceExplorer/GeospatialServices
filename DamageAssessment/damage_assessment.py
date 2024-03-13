import rioxarray as rxr
import xarray as xr
from rasterio.errors import NotGeoreferencedWarning
import warnings
import matplotlib.pyplot as plt

BUILDING_AREA = './data/WSF3d_V02_BuildingArea.tif'
BELIZE = './data/belize-sfincs_map.nc'

def main():
    buildings = rxr.open_rasterio(
        BUILDING_AREA
    ).isel(band=0)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=NotGeoreferencedWarning,
            module="rasterio",
        )
        belize_flooding = rxr.open_rasterio(BELIZE, decode_times=False)[0].isel(band=0, timemax=2, time=2)
        print(belize_flooding)
        belize_flooding.hmax.plot()
        plt.savefig('./test.png')
    

if __name__ == "__main__":
    main()