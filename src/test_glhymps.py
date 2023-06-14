# coding:utf-8

import numpy as np
import os
import matplotlib.pyplot as plt
import rasterio as rio
from rasterio.plot import plotting_extent
from rasterio.mask import mask
from shapely.geometry import mapping
import geopandas as gpd
import earthpy as et
import gdal
from osgeo import osr
from osgeo import ogr
from osgeo import gdalconst

ndsm = 'data/MNT_TOPO_BATH_75m.tif'
shp = 'data/GLHYMPS2.0.shp'
data = gdal.Open(ndsm, gdalconst.GA_ReadOnly)
geo_transform = data.GetGeoTransform()
#source_layer = data.GetLayer()
x_min = geo_transform[0]
y_max = geo_transform[3]
x_max = x_min + geo_transform[1] * data.RasterXSize
y_min = y_max + geo_transform[5] * data.RasterYSize
x_res = data.RasterXSize
y_res = data.RasterYSize
mb_v = ogr.Open(shp)
mb_l = mb_v.GetLayer()
pixel_width = geo_transform[1]
output = 'data/test.tif'
target_ds = gdal.GetDriverByName('GTiff').Create(output, x_res, y_res, 1, gdal.GDT_Float32)
target_ds.SetGeoTransform((x_min, pixel_width, 0, y_max, 0,pixel_width))
band = target_ds.GetRasterBand(1)
NoData_value = -999999
band.SetNoDataValue(NoData_value)
band.FlushCache()
gdal.RasterizeLayer(target_ds, [1], mb_l, options=["ATTRIBUTE=%s" %'logK_Ferr_',"INVERSE=FALSE"])
target_ds_data = target_ds.GetRasterBand(1).ReadAsArray()
target_ds = None


dem = gdal.Open('data/test.tif')
dem_data = dem.GetRasterBand(1).ReadAsArray()
plt.figure()
plt.imshow(dem_data)
plt.show()
a=1