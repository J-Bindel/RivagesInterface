# import os, sys
# from osgeo import gdal, gdalconst
# from osgeo import osr, ogr
# import pandas as pd
# import get_geological_structure as ggs
# import numpy





# # Variables
site_number = 1
# sites = pd.read_table(os.path.dirname(os.path.abspath(__file__)) + "/data/study_sites.txt", sep='\s+', header=0, index_col=0)
# coord = sites._get_values[site_number, 1:5]


# path_to_mask = "/DATA/These/OSUR/Extract_BV_june/" + str(site_number) + "_Mask.tif"
# #print("r_dem", r_dem)
# dataset = gdal.Open(path_to_mask)
# array= numpy.array(dataset.ReadAsArray())
# # for x in range(1, dataset.RasterCount + 1):
# #     band = dataset.GetRasterBand(x)
# #     array = band.ReadAsArray()
# #     print("x: ", x)

# print(array)

import numpy as np
import gdal

site_number = 1
ds = gdal.Open("/DATA/These/OSUR/Extract_BV_june/" + str(site_number) + "_Mask.tif")
print(ds)
cols = ds.RasterXSize
rows = ds.RasterYSize
print(cols, rows)
myarray = np.array(ds.GetRasterBand(1).ReadAsArray())

for c in range(cols):
    for r in range(rows):
        if np.isnan(myarray[r][c]):
            #print("nope nan")
            pass
        else:
            print("yep mask")

# print(myarray)
# myarray[~np.isnan(myarray)]=1
# myarray[np.isnan(myarray)]=0
# print(myarray)


#         if myarray[c][r]==1:
#             print("Yesss!")