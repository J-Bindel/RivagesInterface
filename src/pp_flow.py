import flopy
from flopy.export import vtk as fv
import os
import sys
import flopy.utils.binaryfile as fpu
import flopy.utils.formattedfile as ff
import numpy as np
import pandas as pd
from osgeo import gdal
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rc
from matplotlib import cm
from pysheds.grid import Grid
import rasterio
import elevation
import src.get_geological_structure as ggs

modelname = 'H:/Users/gauvain/DEM/Breville-Sur-Mer/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1' \
            '/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1'
mf1 = flopy.modflow.Modflow.load(modelname + '.nam', verbose=False, check=False, load_only=["bas6", "dis"])
bas = flopy.modflow.ModflowBas.load(modelname + '.bas', mf1)
dis = flopy.modflow.ModflowDis.load(modelname + '.dis', mf1)
rchbase = flopy.modflow.ModflowRch.load(modelname + '.rch', mf1)
hds = fpu.HeadFile(modelname+'.hds')
head = hds.get_alldata()
times = hds.get_times()
kstpkper = hds.get_kstpkper()

cbb = fpu.CellBudgetFile(modelname + '.cbc')
CBB = cbb.get_data(kstpkper=(0, 0))
drn_flow = np.zeros((dis.nrow, dis.ncol))
for sim in range(0, 7):
    kstpkper = (0, sim)
    frf = cbb.get_data(text='FLOW RIGHT FACE', kstpkper=kstpkper)[0]
    fff = cbb.get_data(text='FLOW FRONT FACE', kstpkper=kstpkper)[0]
    flf = cbb.get_data(text='FLOW LOWER FACE', kstpkper=kstpkper)[0]
    drain = cbb.get_data(text='DRAINS', kstpkper=kstpkper)
    rch = cbb.get_data(text='RECHARGE', kstpkper=kstpkper)[0][1]
lay = 2
for i in range(0, dis.nrow):
    for j in range(0, dis.ncol):
        if sum(frf[0:lay, i, j]) < 0:
            drn_flow[i, j] = drn_flow[i, j] - sum(frf[0:lay, i, j])
        if sum(fff[0:lay, i, j]) < 0:
            drn_flow[i, j] = drn_flow[i, j] - sum(fff[0:lay, i, j])
        if sum(flf[0:lay, i, j]) < 0:
            drn_flow[i, j] = drn_flow[i, j] - sum(flf[0:lay, i, j])
        if ((i > 0) and (i < dis.nrow-1) and (j > 0) and (j < dis.ncol-1) ):
            if sum(frf[0:lay, i, j-1]) > 0:
                drn_flow[i, j] = drn_flow[i, j] + sum(frf[0:lay, i, j-1])
            if sum(fff[0:lay, i-1, j]) > 0:
                drn_flow[i, j] = drn_flow[i, j] + sum(fff[0:lay, i-1, j])

def plotFigure(data, label, cmap='Blues'):
    plt.figure(figsize=(12,10))
    plt.imshow(data, extent=grid.extent, cmap=cmap)
    plt.colorbar(label=label)
    plt.grid()

grid = Grid.from_raster('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT.tif', data_name='dem')
plotFigure(grid.dem, 'Elevation (m)')
grid.fill_depressions('dem', out_name='flooded_dem')
depression = grid.detect_depressions('dem')
a = depression.any()
grid.resolve_flats('flooded_dem', out_name='inflated_dem')
dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
grid.flowdir(data='inflated_dem', out_name='dir', dirmap=dirmap, routing='d8', nodata_out=0)
plotFigure(grid.dir,'Flow Directiom','viridis')
grid.view('dir')
x, y = 367025, 6880210
grid.catchment(data='dir', x=x, y=y, dirmap=dirmap, out_name='catch',
               recursionlimit=15000, xytype='label',ignore_metadata=False, routing='d8', nodata_out=0)
grid.flowdir(data='catch', out_name='dir', dirmap=dirmap, routing='d8')
plotFigure(grid.dir,'Flow Directiom','viridis')
grid.accumulation(data='catch', dirmap=dirmap, out_name='acc', routing='d8', nodata_out=0)
plotFigure(grid.acc,"Cell Number",'PuRd')

slope1=gdal.DEMProcessing('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_Slope.tif','H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT.tif', 'slope')
with rasterio.open('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_Slope.tif') as dataset:
    slope = dataset.read(1)
slope = np.gradient(dis.top._array, axis=0)

plt.show()
plt.figure()
plt.imshow(drn_flow, cmap='jet', vmax=400)
plt.colorbar()

plt.figure()
plt.imshow(grid.dir, cmap='jet', vmax=5)
plt.colorbar()

plt.figure()
plt.imshow(grid.acc, cmap='jet', vmax=100)
plt.colorbar()

fig=plt.figure()
ax = fig.add_subplot(1, 1, 1)
plt.scatter(grid.acc,np.abs(slope), cmap='jet')
ax.set_yscale('log')
ax.set_xscale('log')
plt.xlim((0.01,1000))
plt.ylim((0.001,1000))

fig1=plt.figure()
ax = fig1.add_subplot(1, 1, 1)
plt.scatter(grid.acc,drn_flow, cmap='jet')
ax.set_yscale('log')
ax.set_xscale('log')
plt.xlim((0.01,1000))
plt.ylim((0.001,1000))

slope[grid.acc==0]=0

fig1=plt.figure()
ax = fig1.add_subplot(1, 1, 1)
plt.scatter(slope,drn_flow, cmap='jet')
ax.set_yscale('log')
ax.set_xscale('log')
plt.xlim((0.01,1000))
plt.ylim((0.001,1000))

plt.show()