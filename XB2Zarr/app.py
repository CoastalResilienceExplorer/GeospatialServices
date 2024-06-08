from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

import os, uvicorn, io
import xarray as xr
import rioxarray as rxr
from NetCDF_Multi_Function_Tool import write_timestep_images, get_bounds, transform_coords
import uuid, shutil

app = FastAPI()


@app.post("/files/")
async def create_file(
    xboutput: Annotated[bytes, File()],
    id: Annotated[str, Form()],
    vars: Annotated[str, Form()],
):
    xid = str(uuid.uuid1())
    vars = vars.split(',')
    print(vars)
    output_base_dir = os.path.join("/tmp", xid)
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    ds = xr.open_dataset(io.BytesIO(xboutput))
    bounds = get_bounds(ds)
    nx_max = ds.nx.max()
    ny_max = ds.ny.max()
    outputs = []
    for var in vars:
        print(var)
        if var == "zs":
            tdim="globaltime"
        else:
            tdim="meantime"
        output_dir = os.path.join(output_base_dir, var)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        write_timestep_images(ds, output_dir, 0, 8, var, tdim)
        if not os.path.exists("/results"):
            os.makedirs("/results")
        results_dir = f"/results/{xid}"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        output_zarr = os.path.join(output_dir, f"{id}.zarr")
        output_nc = os.path.join(output_dir, f"{id}.nc")
        datasets = [
            transform_coords(rxr.open_rasterio(os.path.join(output_dir, i)), nx_max, ny_max, bounds).rio.write_crs(ds.attrs['crs']).rio.write_nodata(-1000)\
                .expand_dims({"time": 1})\
                .assign_coords({"time": [int(i.split('.')[0].split('_')[-1])]}) 
                for i in os.listdir(output_dir)
        ]
        # xr.concat(
        #     datasets,
        #     dim="time"
        # ).to_zarr(output_zarr)
        x = xr.concat(
            datasets,
            dim="time"
        ).rename(var)
        x.to_netcdf(output_nc)
        outputs.append(x)
    xr.merge(outputs).to_netcdf(os.path.join(output_base_dir, 'combined.nc'))
    shutil.make_archive(os.path.join(results_dir, "results"), "zip", output_base_dir)
    return FileResponse(os.path.join(results_dir, "results.zip"))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
