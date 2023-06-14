# -*- coding: utf-8 -*-
import numpy as np
from osgeo import gdal, osr
import matplotlib.pyplot as plt
import flopy
import flopy.utils.binaryfile as fpu
import get_geological_structure as ggs
import pandas as pd

def get_path(bassin_versant, precipitation, parameter, resolution):
    # rainfall = np.around(precipitation*1e-3/3600, decimals=1)
    BV = bassin_versant
    precipitation = precipitation
    resolution = resolution
    param = parameter
    Filename = BV + "_" + str(resolution) + "m.10." + param
    path_to_file = 'H:/Users/gauvain/EROS/test/' + BV + '/' + 'precipitation(' + str(precipitation) + ')/' + str(
        resolution) + 'm/'

    return path_to_file, Filename


def open_file(path_to_file):
    with open(path_to_file, 'rb') as f:
        # Read and store header
        hdr = np.fromfile(f, np.short, 2)

        # Read and store raster properties
        sizeX = int(np.fromfile(f, np.short, count=1))  # grd width
        sizeY = int(np.fromfile(f, np.short, count=1))  # grd length
        xyzlohi = np.fromfile(f, np.double, count=6)  # min/max values of x,y,z

        # Scale computation
        cs = (xyzlohi[1] - xyzlohi[0]) / (sizeX - 1)  # cellsize

        # Read grid values and store them in a matrix
        grd = np.fromfile(f, np.float32).reshape((sizeY, sizeX), order='C')

        return grd, sizeX, sizeY, cs


def write(grd, sizeX, sizeY, cs, output_file):
    with open(output_file, 'wb') as fid:
        # Write header
        np.array("DSBB", dtype=np.character).tofile(fid)
        np.array(sizeX, dtype=np.short).tofile(fid)
        np.array(sizeY, dtype=np.short).tofile(fid)
        np.array(0, dtype=np.double).tofile(fid)
        np.array((sizeX - 1) * cs, dtype=np.double).tofile(fid)
        np.array(0, dtype=np.double).tofile(fid)
        np.array((sizeY - 1) * cs, dtype=np.double).tofile(fid)
        np.array(np.min(np.min(grd)), dtype=np.double).tofile(fid)
        np.array(np.max(np.max(grd)), dtype=np.double).tofile(fid)

        # Write data
        np.array(grd, dtype=np.float32).tofile(fid)

        fid.close()


#ggs.save_clip_dem(site_number=1)
#ggs.save_clip_lidar(site_number=1)
#ggs.save_clip_mnt5m(site_number=1)

r_lidar = ('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_lidar1m.tif')
lidar = gdal.Open(r_lidar)
lidar_geot = lidar.GetGeoTransform()
lidar_data = lidar.GetRasterBand(1).ReadAsArray()
r_dem = ('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT.tif')
dem = gdal.Open(r_dem)
dem_geot = dem.GetGeoTransform()
dem_data = dem.GetRasterBand(1).ReadAsArray()
#dem_data=dem_data.repeat(75, axis=0).repeat(75,axis=1)

water_level = open_file('H:/Users/gauvain/EROS/test/h/alt=test.time_end=30.time_draw=1.time_step=0.125/test.1.water')
water_level[0][water_level[0]<0.01]=0
topo = open_file('H:/Users/gauvain/EROS/test/h/alt=test.time_end=30.time_draw=1.time_step=0.125/test.1.alt')
site_number = 1
sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
coord = sites._get_values[site_number, 1:5]
drv = gdal.GetDriverByName("GTiff")
ds = drv.Create(sites.index._data[site_number] + '/' + sites.index._data[site_number] + '_water_level.tif',
                int(water_level[1]), int(water_level[2]), 1, gdal.GDT_Float32)
srs = osr.SpatialReference()
srs.ImportFromEPSG(2154)
ds.SetProjection(srs.ExportToWkt())
gt = [lidar_geot[0], water_level[3], 0,lidar_geot[3], 0,-water_level[3]]
ds.SetGeoTransform(gt)
a=topo[0]+water_level[0]
a[water_level[0]==0]=-9999
ds.GetRasterBand(1).WriteArray(a[::-1])
ds.GetRasterBand(1).SetNoDataValue(-9999)
del ds
#lidar_data[lidar_data==np.min(lidar_data)]=dem_data[lidar_data==np.min(lidar_data)]


modelname = 'H:/Users/gauvain/DEM/Breville-Sur-Mer/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1'
mf1 = flopy.modflow.Modflow.load(modelname + '.nam', verbose=False, check=False, load_only=["bas6", "dis"])
bas = flopy.modflow.ModflowBas.load(modelname + '.bas', mf1)
dis = flopy.modflow.ModflowDis.load(modelname + '.dis', mf1)
upw = flopy.modflow.ModflowUpw.load(modelname + '.upw', mf1)
rchbase = flopy.modflow.ModflowRch.load(modelname + '.rch', mf1)
hds = fpu.HeadFile(modelname + '.hds')
head = hds.get_alldata()
times = hds.get_times()
kstpkper = hds.get_kstpkper()

cbb = fpu.CellBudgetFile(modelname + '.cbc')
CBB = cbb.get_data(kstpkper=(0, 0))
drn_flow = np.ones((7, dis.nrow, dis.ncol))
drn_area = np.ones((7, dis.nrow, dis.ncol), dtype=float)
for sim in range(0, 7):
    kstpkper = (0, sim)
    frf = cbb.get_data(text='FLOW RIGHT FACE', kstpkper=kstpkper)[0]
    fff = cbb.get_data(text='FLOW FRONT FACE', kstpkper=kstpkper)[0]
    flf = cbb.get_data(text='FLOW LOWER FACE', kstpkper=kstpkper)[0]
    drain = cbb.get_data(text='DRAINS', kstpkper=kstpkper)
    rch = cbb.get_data(text='RECHARGE', kstpkper=kstpkper)[0][1]
    count = 0
    rch_unit = np.max(rch) / 75 / 75
    for i in range(0, dis.nrow):
        for j in range(0, dis.ncol):
            drn_flow[sim, i, j] = drain[0][count][1]
            drn_area[sim, i, j] = np.abs(drn_flow[sim, i, j]) / rch_unit
            count = count + 1
    drn_flow[sim] = np.abs(drn_flow[sim])/ 24 / 60 / 60
    print(np.sum(drn_flow[sim]))
    drn_flow[sim] = drn_flow[sim]
    drn_flow[sim][bas.ibound.array[0] == -1] = -1
    drn_flow[sim,:,0] = -1
    drn_flow[sim, :, -1] = -1
    drn_flow[sim, 0, :] = -1
    drn_flow[sim, -1, :] = -1

site_number = 1
sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
coord = sites._get_values[site_number, 1:5]
ulY, lrY, ulX, lrX, clip_dem_x, clip_dem_y = ggs.get_model_size(coord)

sim = 2
drn_flow_lidar = drn_flow[sim].repeat(75, axis=0).repeat(75,axis=1)
drn_flow_lidar[lidar_data==int(-9999)]=0

def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

cell_size = 75
lidar_data = rebin(lidar_data,[int(lidar_data.shape[0]/cell_size),int(lidar_data.shape[1]/cell_size)])
drn_flow_lidar = rebin(drn_flow_lidar,[int(drn_flow_lidar.shape[0]/cell_size),int(drn_flow_lidar.shape[1]/cell_size)])
sizeX = lidar_data.shape[1]
sizeY = lidar_data.shape[0]
lidar_data[lidar_data<-100]=int(-9999)

plt.figure()
plt.imshow(drn_flow[sim], vmin=0)
plt.figure()
plt.imshow(dem_data)

write(np.flip(dem_data,0), sizeX, sizeY, cell_size, 'H:/Users/gauvain/EROS/test/Topo/test.alt')
write(np.flip(drn_flow[sim],0), sizeX, sizeY, cell_size, 'H:/Users/gauvain/EROS/test/Topo/test.rain')

#plt.show()
a = 1