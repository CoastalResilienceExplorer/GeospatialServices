# https://gdal.org/programs/gdal_grid.html
gdal_grid -a linear -txe 623000 625000 -tye 8359000 8361000 -outsize 400 400 -of GTiff -ot Float64 -l dem test.vrt dem.tiff