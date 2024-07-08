import rioxarray as rxr
import requests, os
from utils.dataset import makeSafe_rio
from utils.get_features import get_features_with_z_values
from nsi_assessment import get_nsi_damages_generic

BASEDIR = "/app/damage_data/USVI_data/flooding/USGS_USVI/"


for i in os.listdir(BASEDIR):
    flooding = rxr.open_rasterio(
        os.path.join(BASEDIR, i)
    ).isel(band=0)
    print(flooding)
    flooding = makeSafe_rio(flooding)
    flooddepths = get_features_with_z_values(flooding, ISO3="USA")
    damages = get_nsi_damages_generic(flooddepths)
    damages.drop(columns=['polygon'], inplace=True)
    outdir = os.path.join('/app/data/USGS_USVI/block')
    if not os.path.exists(outdir):  
        os.makedirs(outdir)
    damages.to_file(os.path.join(outdir, f'{i.split(".")[0]}.gpkg'))