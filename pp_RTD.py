# coding:utf-8

import os
from IPython.core.debugger import set_trace as st
import numpy as np
import flopy
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import seaborn as sns
import pandas as pd
import flopy.utils.binaryfile as fpu
from matplotlib import cm
import seaborn as sns
from statsmodels.nonparametric.kde import KDEUnivariate
import matplotlib.pylab as pl
import matplotlib as mpl
from scipy.optimize import curve_fit
from scipy import integrate
from scipy.special import gamma
from scipy.stats import norm
import matplotlib.tri as tri
from matplotlib import colors as mcolors
from matplotlib import rc
from osgeo import gdal, gdalconst
from osgeo import osr, ogr

def create_files(modelfolder):
    for files in range (0, len(modelfolder)):
        BV_data = get_watershed()
        modelname = modelfolder[files].split('/')[5]
    
        mf1 = flopy.modflow.Modflow.load(modelname+'.nam',model_ws=modelfolder[files], verbose=False, check=False)
        ncol = mf1.ncol
        nrow = mf1.nrow
        cbb = fpu.CellBudgetFile(modelfolder[files]+ '/' + modelname +'.cbc')
        # cbb.list_records()
        rec_drn = cbb.get_data(kstpkper=(0, 0), text='DRAINS')
        rec_rch = cbb.get_data(kstpkper=(0, 0), text='RECHARGE')
    
        drn = np.ones((nrow,ncol))
        compti = 0
        comptj = 0
        for ii in range(0, rec_drn[0].shape[0]):
            drn[compti, comptj] = -1 * rec_drn[0][ii][1]
            comptj += 1
            if comptj == ncol:
                compti += 1
                comptj = 0
        rch = rec_rch[0][1]
        weight = drn / rch
        weight[weight<0] = 0
        weight[weight>1] = 1
        weight[BV_data == 0]= np.nan
        weight = 1-weight
    
        Stot = np.nansum(~np.isnan(weight))
        Sseep = np.nansum(1-weight)
        perc_Sseep = np.ones((1))
        perc_Sseep[0] = Sseep/Stot
    
        np.savetxt(modelfolder[files] + "/perc_seepage.csv", perc_Sseep)
    
        endobj = flopy.utils.EndpointFile(modelfolder[files] + '/' + modelname +'.mpend')
        endpt = endobj.get_alldata()
    
        time = np.ones(BV_data.shape)*np.nan
        times = []
        weights =[]
        for i in range (0, BV_data.shape[0]):
            for j in range (0, BV_data.shape[1]):
                if BV_data[i,j] == 1:
                    time_cell = endpt.time[(endpt.i0 == i) & (endpt.j0 == j)]
                    for k in range (0, len(time_cell)):
                        times.append(time_cell[k])
                        weights.append(weight[i,j])
                    time[i,j] = np.nanmean(time_cell)
    
        weights = np.asarray(weights)
        times = np.asarray(times)
        np.savetxt(modelfolder[files] + "/mean_time_spatial.csv", time)
        np.savetxt(modelfolder[files] + "/time.csv", times)
        np.savetxt(modelfolder[files] + "/weight_spatial.csv", weight)
        np.savetxt(modelfolder[files] + "/weight.csv", weights)
    
        moments= np.ones(4)
        moments[0] = np.average(times, weights=weights) #mean
        moments[1] = np.average(((times - moments[0]) ** 2), weights=weights) #variance
        moments[2] = np.sqrt(moments[1]) #standard deviation
        time1 = times / moments[0]
        moments[3] = moments[2] / moments[0] #CV 

        np.savetxt(modelfolder[files] + "/moments.csv", moments)
        
        kde1 = KDEUnivariate(time1)
        kde1.fit(bw='scott', fft=False, gridsize=200, weights=weights, clip=(0, 10))
        t = kde1.support
        pt = [kde1.evaluate(xi) for xi in kde1.support]
    
        np.savetxt(modelfolder[files] + "/time_dist.csv", t)
        np.savetxt(modelfolder[files] + "/dist_dist.csv", pt)
    
    

def load_files(modelfolder):
    time_sp = np.loadtxt(modelfolder+"/mean_time_spatial.csv")
    times = np.loadtxt(modelfolder+"/time.csv")
    weight_sp = np.loadtxt(modelfolder+"/weight_spatial.csv")
    weights = np.loadtxt(modelfolder+"/weight.csv")
    t = np.loadtxt(modelfolder+"/time_dist.csv")
    pt = np.loadtxt(modelfolder+"/dist_dist.csv")
    perc_seep = np.loadtxt(modelfolder+"/perc_seepage.csv")
    moments = np.loadtxt(modelfolder+"/moments.csv")
    
    return time_sp, times, weight_sp, weights, t, pt, perc_seep, moments
    
def get_watershed():
    r_dem = "H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT_bassins.tif"
    dem = gdal.Open(r_dem)
    dem_data = dem.GetRasterBand(1).ReadAsArray()
    return dem_data

def display(modelfolder):
    fig1 = plt.figure(figsize=(5,5))
    ax1 = fig1.add_subplot(111)
    fig2= plt.figure(figsize=(5,5))
    ax2= fig2.add_subplot(111)
    
    for i in range (0, len(modelfolder)):
        time_sp, times, weight_sp, weights, t, pt, perc_seep, moments= load_files(modelfolder[i])
        ax1.plot(t,pt)
        ax2.scatter(perc_seep*100, moments[3])
        x1 = np.linspace(0, 100, 100)
        y1 = (1)-np.log(1-(x1/100))
        ax2.plot(x1,y1, 'k-', lw = 3, label=r'$CV =\frac{1}{\sqrt{3}}- log(1-\frac{S_{seepage}}{S_{total}})$')
    plt.show() 
    
def export_DEM_watertable(modelfolder):
    for files in range (0, len(modelfolder)):
        modelname = modelfolder[files].split('/')[5]
        mf1 = flopy.modflow.Modflow.load(modelname+'.nam',model_ws=modelfolder[files], verbose=False, check=False)
        nlay = mf1.nlay
        ncol = mf1.ncol
        nrow = mf1.nrow
        hds_1c = fpu.HeadFile(modelfolder[files]+'/'+modelname+'.hds')
        head_1c = hds_1c.get_alldata(mflay=None)
        head = np.ones((nrow, ncol)) * np.nan
        for i in range(0, nrow):
            for j in range(0, ncol):
                for k in range(0, nlay):
                    if head_1c[0][k][i, j] != -100.:
                        head[i, j] = head_1c[0][k][i, j]
                        break
                        
        dem = gdal.Open('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT.tif')
        geot = dem.GetGeoTransform()
        dem_data = head
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(modelfolder[files]+'/'+modelname+'_MNT_watertable.tif',
                        dem_data.shape[1], dem_data.shape[0], 1, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(2154)
        ds.SetProjection(srs.ExportToWkt())
        gt = [geot[0], geot[1], 0, geot[3], 0, geot[5]]
        ds.SetGeoTransform(gt)
        ds.GetRasterBand(1).WriteArray(dem_data)

def export_DEM_aquifer_thickness(modelfolder):
    for files in range (0, len(modelfolder)):
        modelname = modelfolder[files].split('/')[5]
        mf1 = flopy.modflow.Modflow.load(modelname+'.nam',model_ws=modelfolder[files], verbose=False, check=False)
        nlay = mf1.nlay
        ncol = mf1.ncol
        nrow = mf1.nrow
        zbot = mf1.bot
        print(zbot)
        hds_1c = fpu.HeadFile(modelfolder[files]+'/'+modelname+'.hds')
        head_1c = hds_1c.get_alldata(mflay=None)
        head = np.ones((nrow, ncol)) * np.nan
        for i in range(0, nrow):
            for j in range(0, ncol):
                for k in range(0, nlay):
                    if head_1c[0][k][i, j] != -100.:
                        head[i, j] = head_1c[0][k][i, j]
                        break
                        
        dem = gdal.Open('H:/Users/gauvain/DEM/Breville-Sur-Mer/Breville-Sur-Mer_MNT.tif')
        
        geot = dem.GetGeoTransform()
        dem_data = head
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(modelfolder[files]+'/'+modelname+'_MNT_watertable.tif',
                        dem_data.shape[1], dem_data.shape[0], 1, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(2154)
        ds.SetProjection(srs.ExportToWkt())
        gt = [geot[0], geot[1], 0, geot[3], 0, geot[5]]
        ds.SetGeoTransform(gt)
        ds.GetRasterBand(1).WriteArray(dem_data)
        
    
    
    