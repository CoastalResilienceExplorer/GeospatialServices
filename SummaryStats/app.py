import os
import logging
import flask
from flask import Flask, request
import xarray as xr
import rioxarray as rxr
import geopandas as gpd
import pandas as pd
from glob import glob
from utils.geo import clip_dataarray_by_geometries
from utils.dataset import open_as_ds

logging.basicConfig()
logging.root.setLevel(logging.INFO)

app = Flask(__name__)


def summary_stats(gdf: gpd.GeoDataFrame, ds: xr.DataArray | xr.Dataset):
    data = clip_dataarray_by_geometries(ds, gdf)
    
    def safe_stats(grid):
        return {
            "max": grid.max().to_array().to_dataframe(name="max"),
            "sum": grid.sum().to_array().to_dataframe(name="sum"),
            "mean": grid.mean().to_array().to_dataframe(name="mean"),
            "count": grid.count().to_array().to_dataframe(name="count")
        }
    
    
    data = [safe_stats(d) for d in data]
    
    df_buff = []
    for idx, d in enumerate(data):
        series_buff = []
        for k in ('max', 'sum', 'mean', "count"):
            v = d[k].reset_index()
            cols = v.index
            logging.info(cols)
            v['idx'] = idx
            v = v.pivot(index='idx', columns='variable', values=k)
            v = v.rename(columns={c: f'{c}_{k}' for c in v.columns})
            series_buff.append(v)
            
        merged_df =pd.concat(series_buff, axis=1)
        df_buff.append(merged_df)
    
    return pd.concat([gdf, pd.concat(df_buff)], axis=1)
        
            


@app.route('/summary_stats/', methods=["POST"])
def api_summary_stats():
    fname = os.path.join('/tmp', request.files['geographies'].filename.split('/')[-1])
    logging.info(fname)
    with open(fname, 'wb') as f:
        f.write(request.files['geographies'].read())
    gdf = gpd.read_file(
        fname, driver="GPKG"
    )
    logging.info(request.form)
    input_path = os.path.join(os.getenv('MOUNT_PATH'), request.form['project'], request.form['key'], request.form['data_type'])
    
    output_name = request.files['geographies'].filename.split('/')[-1].split('.')[0] + f'_{request.form["data_type"]}'
    output_path = os.path.join(os.getenv('MOUNT_PATH'), request.form['project'], request.form['key'], request.form['data_type'], 'summary_stats')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    ds = open_as_ds(input_path)
    CRS = ds.rio.crs
    gdf = gdf.to_crs(CRS)
    stats = summary_stats(gdf, ds)
    stats.to_parquet(os.path.join(output_path, f'{output_name}.parquet'))
    stats.to_file(os.path.join(output_path, f'{output_name}.gpkg'))

    return ("complete", 200)



@app.get("/")
def test():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
