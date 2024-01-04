from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

import os, uvicorn, io
import xarray as xr
import rioxarray as rxr
from NetCDF_Multi_Function_Tool import write_timestep_images, get_bounds
import uuid, shutil

app = FastAPI()


@app.post("/files/")
async def create_file(
    xboutput: Annotated[bytes, File()],
    id: Annotated[str, Form()],
):
    xid = str(uuid.uuid1())
    output_dir = os.path.join("/tmp", xid)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ds = xr.open_dataset(io.BytesIO(xboutput), chunks={"globaltime": 500})
    print(get_bounds(ds))
    return
    write_timestep_images(ds, output_dir, 0, 2, "zs", "globaltime")
    print(os.listdir(output_dir))
    print("file written, sending...")
    if not os.path.exists("/results"):
        os.makedirs("/results")
    results_dir = f"/results/{xid}"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    output_zarr = os.path.join(output_dir, f"{id}.zarr")
    datasets = [
        rxr.open_rasterio(os.path.join(output_dir, i))\
            .expand_dims({"time": 1})\
            .assign_coords({"time": [int(i.split('.')[0].split('_')[-1])]}) 
            for i in os.listdir(output_dir)
    ]
    print(datasets[0])
    xr.concat(
        datasets,
        dim="time"
    ).to_zarr(output_zarr)
    shutil.make_archive(os.path.join(results_dir, "results"), "zip", output_dir)
    return FileResponse(os.path.join(results_dir, "results.zip"))


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
