import xarray as xr

z = 'gs://cogmaker-output-staging/NBS_ADAPTS/JAM/damages/damages.zarr'
# z = 'data/damages_test.zarr'

ds = xr.open_zarr(z)

print(ds.attrs)
print(ds.rio.crs)