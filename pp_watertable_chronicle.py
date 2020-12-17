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
import matplotlib.dates as md
import elevation
import richdem as rd
from datetime import datetime
import get_geological_structure as ggs

sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
site_number = 3 #Select site number
coord = sites._get_values[site_number,1:5]

geot, geotx, geoty, demData = ggs.get_clip_dem(coord)

with open("data/watertable_chronicle/chroniques_lessay.txt") as ins:
    chronicles = ins.readlines()
for i in range (0,len(chronicles)):
    chronicles[i] = chronicles[i].split("|")

x_coord = int(chronicles[1][18])
y_coord = int(chronicles[1][19])
watertable_chronicle= np.ones(len(chronicles)-1)
date_time = []
for i in range (1, len(chronicles)):
    watertable_chronicle[i-1] = float(chronicles[i][5])
    date_time.append(datetime.strptime(chronicles[i][3], '%d/%m/%Y %H:%M:%S'))
dates = md.date2num(date_time)

idx = (np.abs(geotx - x_coord)).argmin()
idy = (np.abs(geoty - y_coord)).argmin()

modelname = ["" for x in range(5)]
modelname[0] ='H:/Users/gauvain/DEM/Agon-Coutainville/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1/model_time_0_geo_0_thick_1_K_86.4_Sy_0.1'
modelname[1] ='H:/Users/gauvain/DEM/Agon-Coutainville/model_time_0_geo_0_thick_1_K_8.64_Sy_0.1/model_time_0_geo_0_thick_1_K_8.64_Sy_0.1'
modelname[2] ='H:/Users/gauvain/DEM/Agon-Coutainville/model_time_0_geo_0_thick_1_K_0.864_Sy_0.1/model_time_0_geo_0_thick_1_K_0.864_Sy_0.1'
modelname[3] ='H:/Users/gauvain/DEM/Agon-Coutainville/model_time_0_geo_0_thick_1_K_8.64_Sy_0.2/model_time_0_geo_0_thick_1_K_8.64_Sy_0.2'
modelname[4] ='H:/Users/gauvain/DEM/Agon-Coutainville/model_time_0_geo_0_thick_1_K_8.64_Sy_0.05/model_time_0_geo_0_thick_1_K_8.64_Sy_0.05'
plt.figure()
#plt.plot(dates,watertable_chronicle)

p=[[] for x in range(5)]
for n in range (0,1):
    print(n)
    mf1 = flopy.modflow.Modflow.load(modelname[n] + '.nam', verbose=False, check=False, load_only=["bas6", "dis"])
    bas = flopy.modflow.ModflowBas.load(modelname[n] + '.bas', mf1)
    dis = flopy.modflow.ModflowDis.load(modelname[n] + '.dis', mf1)
    hds = fpu.HeadFile(modelname[n]+'.hds')
    head = hds.get_alldata()


    time = np.linspace(md.date2num(datetime.strptime('31/07/1970 00:00:00', '%d/%m/%Y %H:%M:%S')),
                       md.date2num(datetime.strptime('31/07/1970 00:00:00', '%d/%m/%Y %H:%M:%S'))+head.shape[0],head.shape[0])
    head_point = np.ones((head.shape[0]))
    ztop = np.ones((head.shape[0]))
    watertable = np.zeros([head.shape[0],head.shape[2],head.shape[3]])

    for t in range (0, head.shape[0]):
        watertable[t] = np.amax(head[t], axis=0)
        #head_point[t] = watertable[t,idy,idx]
        head_point[t] = watertable[t, 0, 113]
        ztop[t]=dis.top[0,113]
    p[n]=plt.plot(time,head_point)
    plt.plot(time,ztop)
    plt.xlabel('Temps (en jours)')
    plt.ylabel("Niveau d'eau (m)")
#plt.legend(p)
plt.show()
a = 1