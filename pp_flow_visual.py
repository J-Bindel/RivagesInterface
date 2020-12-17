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
from matplotlib import rc
from matplotlib import cm
import elevation
import richdem as rd
import get_geological_structure as ggs

modelname ='H:/Users/gauvain/DEM/Barneville-Carteret/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1/model_time_4_geo_0_thick_1_K_0.864_Sy_0.1'
mf1 = flopy.modflow.Modflow.load(modelname + '.nam', verbose=False, check=False, load_only=["bas6","dis"])
bas = flopy.modflow.ModflowBas.load(modelname + '.bas', mf1)
dis = flopy.modflow.ModflowDis.load(modelname + '.dis', mf1)
rchbase = flopy.modflow.ModflowRch.load(modelname + '.rch', mf1)
hds = fpu.HeadFile(modelname+'.hds')
head = hds.get_alldata()
times = hds.get_times()
kstpkper = hds.get_kstpkper()

cbb = fpu.CellBudgetFile(modelname+'.cbc')
CBB = cbb.get_data(kstpkper = (0,0))
drn_flow = np.ones((7, dis.nrow, dis.ncol))
drn_area = np.ones((7, dis.nrow, dis.ncol), dtype=float)
for sim in range (0,7):
    kstpkper = (0, sim)
    frf = cbb.get_data(text='FLOW RIGHT FACE', kstpkper=kstpkper)[0]
    fff = cbb.get_data(text='FLOW FRONT FACE', kstpkper=kstpkper)[0]
    flf = cbb.get_data(text='FLOW LOWER FACE', kstpkper=kstpkper)[0]
    drain = cbb.get_data(text='DRAINS', kstpkper=kstpkper)
    rch = cbb.get_data(text='RECHARGE', kstpkper=kstpkper)[0][1]
    count = 0
    rch_unit = np.max(rch)/75/75
    for i in range(0, dis.nrow):
        for j in range(0, dis.ncol):
            drn_flow[sim,i, j] = drain[0][count][1]
            drn_area[sim,i, j] = np.abs(drn_flow[sim,i, j]) / rch_unit
            count = count + 1
drn_area[drn_flow==0]=np.nan
drn_flow[drn_flow==0]=np.nan

plt.figure()
for i in range (0,7):
    plt.scatter(drn_area[i],np.abs(drn_flow[i]))
#plt.show()
dem = rd.rdarray(dis.top._array, no_data=-9999)
dem.geotransform = [0,75,0,0,0,-75]
slope = rd.TerrainAttribute(dem, attrib='slope_percentage')
aspect = rd.TerrainAttribute(dem, attrib='aspect')

plt.figure()
plt.imshow(slope)
plt.colorbar()

ggs.save_clip_dem(site_number=6)

plt.figure()
plt.yscale('log')
plt.xscale('log')
plt.ylim(0.001,10)
for i in range (3,4):
    plt.scatter(drn_area[i],slope)

plt.show()





#fig1, ax1 = plt.subplots()
#fig2, ax2 = plt.subplots()
#fig3, ax3 = plt.subplots()
#for i in range (0,flf.shape[1]):
#    for j in range (0, flf.shape[2]):
#        if bas.ibound.array[0,i,j] == 1:
#            if flf[0,i,j]<0:
#                ax1.scatter(flf[0,i,j],dis.top._array[i,j])
#                ax2.scatter(flf[0, i, j], slope[i, j])
#                ax3.scatter(flf[0, i, j], aspect[i, j])
#plt.show()