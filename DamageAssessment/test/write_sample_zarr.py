import xarray as xr
import shutil

ds = xr.open_zarr('gs://cogmaker-output-staging/NBS_ADAPTS/JAM/damages/damages_copy.zarr')
ds = ds.isel(x=slice(1100,1200), y=slice(1000,1100))

shutil.rmtree('data/damages_test.zarr')

ds.to_zarr('data/damages_test.zarr')