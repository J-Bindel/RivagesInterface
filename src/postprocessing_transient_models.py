# coding:utf-8

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

modelname = ["" for x in range(5)]
modelname[0] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_86.4/model_time_0_geo_0_thick_1_K_86.4'
modelname[1] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_8.64/model_time_0_geo_0_thick_1_K_8.64'
modelname[2] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_0.864/model_time_0_geo_0_thick_1_K_0.864'
modelname[3] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_0.0864/model_time_0_geo_0_thick_1_K_0.0864'
modelname[4] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_1_thick_1/model_time_0_geo_1_thick_1'
head=[[] for x in range(5)]
watertable = [[] for x in range(5)]
watertable_max = [[] for x in range(5)]
watertable_min = [[] for x in range(5)]
time_watertable = [[] for x in range(5)]
amplitude = [[] for x in range(5)]
zns_max = [[] for x in range(5)]
for n in range (0,5):
    mf1 = flopy.modflow.Modflow.load(modelname[n] + '.nam', verbose=False, check=False, load_only=["bas6","dis"])
    bas = flopy.modflow.ModflowBas.load(modelname[n] + '.bas', mf1)
    dis = flopy.modflow.ModflowDis.load(modelname[n] + '.dis', mf1)
    hds = fpu.HeadFile(modelname[n]+'.hds')
    head[n] = hds.get_alldata()

    # WATERTABLE FOR EACH STRESS PERIOD
    watertable[n] = np.zeros([head[n].shape[0],head[n].shape[2],head[n].shape[3]])
    for t in range (0, head[n].shape[0]):
        watertable[n][t] = np.amax(head[n][t], axis=0)

    # TIME DURING WATERTABLE IS HIGHER CRITICAL DEPTH
    critical_depth = 0.5
    time_watertable[n] = np.ones([head[n].shape[2], head[n].shape[3]])
    for i in range(0, head[n].shape[2]):
        for j in range(0, head[n].shape[3]):
            test = watertable[n][:, i, j][watertable[n][:, i, j] > dis.top[i, j] - critical_depth]
            count = np.alen(test)
            time_watertable[n][i, j] = count

    # MINIMAL WATERTABLE LEVEL
    watertable_min[n] = np.amin(watertable[n], axis=0)
    watertable_min[n] = np.around(watertable_min[n], decimals=2)

    # MAXIMAL WATERTABLE LEVEL
    watertable_max[n] = np.amax(watertable[n], axis=0)
    watertable_max[n] = np.around(watertable_max[n], decimals=2)

    # AMPLITUDE
    amplitude[n] = watertable_max[n] - watertable_min[n]

    # MAXIMAL UNSATURATED THICKNESS
    zns_max[n] = dis.top._array - watertable_min[n]
    zns_max[n][zns_max[n] < 0] = np.nan
    zns_max[n][zns_max[n] > 10] = np.nan
    zns_max[n][zns_max[n] < 2] = np.nan

amp_max = np.max(amplitude, axis=0)
zns = np.max(zns_max, axis=0)

amp_mean = np.mean(amplitude,axis=0)
zns_mean = np.mean(zns_max, axis=0)

amp_mean[np.isnan(zns_mean)]= np.nan
amp_norm = amp_mean/np.nanmax(amp_mean)
zns_norm = 1-(zns_mean/np.nanmax(zns_mean))

ind = amp_norm + zns_norm

fig1, _axis = plt.subplots(figsize=(20, 4),ncols=3)
axis = _axis.flatten()
znsc = axis[0].imshow(zns_norm,vmin=0,vmax=1)
fig1.colorbar(znsc, ax=axis[0],extend='neither')
ampc = axis[1].imshow(amp_norm,vmin=0,vmax=1)
fig1.colorbar(ampc, ax=axis[1],extend='neither')
indc = axis[2].imshow(ind,vmin=np.nanmin(ind),vmax=np.nanmax(ind))
fig1.colorbar(indc, ax=axis[2],extend='neither')
plt.show()

fig,_axs = plt.subplots(figsize=(20, 4),ncols=4)
fig.subplots_adjust(hspace=0.1)
axs = _axs.flatten()
cset0 = axs[0].imshow(time_watertable,cmap='jet',vmin=0,vmax=731)
axs[0].set_ylabel(r'$K_{homogène} = 10^{-6} m.s^{-1}$', fontsize = 20)
axs[0].set_title("Durée : niveau d'eau supérieur \n à la profondeur critique [jours]")
fig.colorbar(cset0, ax=axs[0],extend='neither')

cset1 = axs[1].imshow(dis.top._array-watertable_min,cmap='jet',vmin=0, vmax=40)
axs[1].set_title("Niveau d'eau minimal atteint \n durant la simulation [mètres]")
fig.colorbar(cset1, ax=axs[1],extend='both')

cset2 = axs[2].imshow(dis.top._array-watertable_max,cmap='jet',vmin=0, vmax=40)
axs[2].set_title("Niveau d'eau maximal atteint \n durant la simulation [mètres]")
fig.colorbar(cset2, ax=axs[2],extend='both')

cset3 = axs[3].imshow(amplitude,cmap='jet',vmin=0, vmax=1)
axs[3].set_title("Différence entre niveau d'eau \nmaximal et minimal [mètres]")
fig.colorbar(cset3, ax=axs[3],extend='max')
#fig.tight_layout()
plt.show()


