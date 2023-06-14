import flopy
from flopy.export import vtk as fv
import os
import sys
import flopy.utils.binaryfile as fpu
import flopy.utils.formattedfile as ff
import numpy as np
import pandas as pd
from osgeo import gdal, osr
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib import cm
import elevation
import richdem as rd
import matplotlib as mpl
import src.get_geological_structure as ggs
mpl.rcParams['mathtext.fontset'] = 'cm'
mpl.rcParams['font.size'] = 12


modelname = ["" for x in range(5)]
modelname[0] ='H:/Users/gauvain/DEM/Baie_du_Cotentin/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1'
modelname[1] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1'
modelname[2] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_0.864_Sy_0.1/model_time_0_geo_0_thick_1_K_0.864_Sy_0.1'
modelname[3] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_8.64_Sy_0.2/model_time_0_geo_0_thick_1_K_8.64_Sy_0.2'
modelname[4] ='H:/Users/gauvain/DEM/Saint-Germain-Sur-Ay/model_time_0_geo_0_thick_1_K_8.64_Sy_0.05/model_time_0_geo_0_thick_1_K_8.64_Sy_0.05'

p=[[] for x in range(5)]
for n in range (0,1):
    mf1 = flopy.modflow.Modflow.load(modelname[n] + '.nam', verbose=False, check=False, load_only=["bas6", "dis"])
    bas = flopy.modflow.ModflowBas.load(modelname[n] + '.bas', mf1)
    dis = flopy.modflow.ModflowDis.load(modelname[n] + '.dis', mf1)
    hds = fpu.HeadFile(modelname[n]+'.hds')
    head = hds.get_alldata()
    times = hds.get_times()
    kstpkper = hds.get_kstpkper()
    H = np.amax(head, axis=1)
    years = int(head.shape[0] / 365)
    start_years = np.linspace(32, 32 + (years - 2) * 365,(years - 1), dtype=int)  # début des années hydrologiques le 1er septembre

    H_max_years = np.ones([years-1,H.shape[1],H.shape[2]])
    H_min_years = np.ones([years - 1, H.shape[1], H.shape[2]])
    for i in range (0, start_years.shape[0]):
        a = np.amax(H[start_years[i]:start_years[i] + 364], axis=0)
        b = np.amin(H[start_years[i]:start_years[i] + 364], axis=0)
        H_max_years[i] = a
        H_min_years[i] = b


    A_years = H_max_years - H_min_years

    H_max_mean = np.mean(H_max_years,axis=0)
    H_min_mean = np.mean(H_min_years, axis=0)
    H_max_sim = np.amax(H,axis = 0)
    H_min_sim = np.amin(H, axis = 0)
    A_sim = H_max_sim - H_min_sim
    A_mean = np.mean(A_years, axis=0)

    fig, _axis = plt.subplots(figsize=(12, 5), ncols=2)
    axis = _axis.flatten()
    thick = dis.top._array - H_min_sim
    H_min= H_min_mean
    Cat = H_min_mean

    Cat[(8<=thick) & (thick<18) & (A_sim > 2)] = 2  # piezo 20m
    Cat[(2 <= thick) & (thick < 8) & (A_sim > 2)] = 1  # piezo 10m
    Cat[(2 <= thick) & (thick < 8) & (A_sim < 2)] = 3  # amplitude faible
    Cat[(8 <= thick) & (thick < 18) & (A_sim < 2)] = 4  # amplitudefaible
    #Cat[(8 <= thick) & (thick < 18) & (A_sim > 8)] = 6  # amplitudefaible
    Cat[(18 <= thick)] = 6  # trop profond
    Cat[(0 <= thick) & (thick < 2)] = 5 # Pas assez profond
    Cat[(thick < 0) & (A_sim == 0)] = np.nan
    Cat[(thick < 0) & (A_sim != 0)] = np.nan


    #Cat[thick > 20] = np.nan

    #axis[1].scatter(A_mean, dis.top.array - H_min_10m, c=dis.top.array)

    #H_min[dis.top.array - H_max_mean < 2] = np.nan

    sc2 = axis[0].scatter(A_sim, thick, c=Cat, cmap='jet')
    axis[0].set_title(r"$Z_{top}(x) - H_{min}(x)$ en fonction de $\Delta(x)$")
    axis[0].set_ylabel(r'$Z_{top}(x) - H_{min}(x)$')
    axis[0].set_xlabel(r'$\Delta(x)$')

    axis[1].set_ylabel(r'$Rows$')
    axis[1].set_xlabel(r'$Columns$')
    im1 = axis[1].imshow(Cat, cmap='jet')
    dirmap=(1 , 2 ,3 ,4 ,5 ,6)
    boundaries = ([0] + sorted(list(dirmap)))
    cbar3 = fig.colorbar(im1, ax=axis[1], boundaries=boundaries, values=sorted(dirmap))
    cbar3.ax.set_yticklabels(['','Cat.1', 'Cat.2', 'Cat.3', 'Cat.4','Cat.5','Cat.6'])
    #cbar3.set_label(r'$$')

    sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
    site_number = 5  # Select site number
    coord = sites._get_values[site_number, 1:5]
    geot, geotx, geoty, demData = ggs.get_clip_dem(coord)
    drv = gdal.GetDriverByName("GTiff")
    ds = drv.Create(sites.index._data[site_number] + '/' + sites.index._data[site_number]+ '_well_loc.tif', Cat.shape[1], Cat.shape[0], 1, gdal.GDT_Float32)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(2154)
    ds.SetProjection(srs.ExportToWkt())
    gt=[geotx[0],geot[1],0,geoty[1],0,geot[5]]
    ds.SetGeoTransform(gt)
    ds.GetRasterBand(1).WriteArray(Cat)

plt.show()
a = 1