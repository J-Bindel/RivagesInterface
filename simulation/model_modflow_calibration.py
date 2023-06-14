# coding:utf-8
import math
import flopy
import flopy.utils.binaryfile as fpu
import os
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from osgeo import gdal
import simulation.get_geological_structure as ggs
from IPython.core.debugger import set_trace as st
from IPython.display import display, Markdown, clear_output
from ipywidgets import HTML, widgets
from osgeo import gdal, gdalconst
from osgeo import osr, ogr
from scipy.ndimage import convolve


class calibration:
    def __init__(self, code,out_calib=widgets.Output()):
        self.display_output = out_calib
        self.site_number = code + '/'
        self.filename = 'C:/Users/alexa/Dropbox/DEM/'
        self.modelname = 'Calibration'
        self.modelfolder = self.filename + self.site_number + 'Calibration'
        self.sitefolder = self.filename + self.site_number
        self.code = code
        self.structure = ggs.structure(self.code)
        self.coord = self.structure.coord
        self.first_calibration_structure()
        try:
            self.ParamValues = np.load(self.sitefolder +'logParamValues.npy')
            self.fuzzy = np.load(self.sitefolder +'fuzzyParam.npy')
            self.FinParamValues = np.load(self.sitefolder +'FinlogParamValues.npy')
            self.Finfuzzy = np.load(self.sitefolder +'FinfuzzyParam.npy')
        except:
            pass
            
    
    def extract_best_temp_model(self):
        self.fuzzy = np.load(self.sitefolder +'fuzzyParam.npy')
        fuzzy_Ea = self.fuzzy[(self.fuzzy[:,1]>0.50) & (self.fuzzy[:,1]<1)]
        paramValues_Ea = self.logParamValues[(self.fuzzy[:,1]>0.50) & (self.fuzzy[:,1]<1)]
        st()
        index = (np.abs(fuzzy_Ea[:,0]-1)).argmin()
        self.predictParamValues = paramValues_Ea[index]
        print(fuzzy_Ea[index,0], fuzzy_Ea[index,1],self.predictParamValues)
        return self.predictParamValues
    
    def extract_best_model(self):
        fuzzy_Ea = self.Finfuzzy[(self.Finfuzzy[:,1]>0.50) & (self.Finfuzzy[:,1]<1)]
        paramValues_Ea = self.FinParamValues[(self.Finfuzzy[:,1]>0.50) & (self.Finfuzzy[:,1]<1)]
        st()
        index = (np.abs(fuzzy_Ea[:,0]-1)).argmin()
        self.calibParamValues = paramValues_Ea[index]
        print(fuzzy_Ea[index,0], fuzzy_Ea[index,1],self.calibParamValues)
        return self.calibParamValues
    
    def run_best_model(self):
        param = self.extract_best_model()
        head = self.runModelForParams(param)
        self.extract_river_network_dem(head)
        
    def extract_watertable_tif(self):
        head = self.run_best_model()
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(self.structure.tmp + 'output_watertable.tif',self.structure.dem.shape[1], self.structure.dem.shape[0], 1, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(2154)
        ds.SetProjection(srs.ExportToWkt())
        gt = [self.structure.dem_x[0],self.structure.geot[1], 0, self.structure.dem_y[1], 0, self.structure.geot[5]]
        ds.SetGeoTransform(gt)
        ds.GetRasterBand(1).WriteArray(head)
        
    def extract_river_network_dem(self,head,name='output_river_network.tif'):
        river = head>=self.structure.dem
        river[self.bas.ibound.array[0]==-1]=False
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(self.sitefolder + 'Output/'+ name,self.structure.dem.shape[1], self.structure.dem.shape[0], 1, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(2154)
        ds.SetProjection(srs.ExportToWkt())
        gt = [self.structure.dem_x[0],self.structure.geot[1], 0, self.structure.dem_y[1], 0, self.structure.geot[5]]
        ds.SetGeoTransform(gt)
        ds.GetRasterBand(1).WriteArray(np.array(river, dtype=int))
        
    def first_calibration_structure(self):
        self.number_structure = np.intersect1d(self.structure.geology,self.structure.geology)
        logK_max = -2
        logK_min = -8
        logK_range = np.logspace(logK_min, logK_max, logK_max-logK_min+1)
        self.logParamValues = np.array([list(i) for i in itertools.product(logK_range.tolist(), repeat=len(self.number_structure))])
    
    def second_calibration_structure(self):
        logK = np.log10(self.predictParamValues)
        logK1_range = np.logspace(np.min(logK[0])-1, np.min(logK[0])+1, 20+1)
        logK2_range = np.logspace(np.min(logK[1])-1, np.min(logK[1])+1, 20+1)
        self.FinlogParamValues = np.array([list(i) for i in itertools.product(logK1_range.tolist(), logK2_range.tolist())])
    
    def run_calibration(self):
        # Create empty array
        self.headArray = np.zeros([self.logParamValues.shape[0],self.structure.dem.shape[0],self.structure.dem.shape[1]])
        self.fuzzyParam = np.zeros([self.logParamValues.shape[0],8])
        # Run model function for every group of params
        for index, param in enumerate(self.logParamValues):
            self.headArray[index] = self.runModelForParams(param)
            self.fuzzyParam[index] = self.get_fuzzy(self.headArray[index])
            with self.display_output:
                clear_output()
                print('La calibration est en cours de réalisation...')
                print('Cela peut prendre plusieurs minutes/heures...')
                display(HTML('''<i class="fa fa-circle-notch fa-spin fa-3x fa-fw"></i>
        <span class="sr-only">Loading...</span>'''))
                print(str(index+1)+'/'+str(self.logParamValues.shape[0]),end='\r')
            print(str(index+1)+'/'+str(self.logParamValues.shape[0]),end='\r')
        np.save(self.sitefolder+'logParamValues',self.logParamValues)
        np.save(self.sitefolder+'headArray',self.headArray)
        np.save(self.sitefolder+'fuzzyParam',self.fuzzyParam)
        """
        param = self.extract_best_temp_model()
        self.second_calibration_structure()
        # Create empty array
        self.headArray = np.zeros([self.FinlogParamValues.shape[0],self.structure.dem.shape[0],self.structure.dem.shape[1]])
        self.fuzzyParam = np.zeros([self.FinlogParamValues.shape[0],8])
        for index, param in enumerate(self.FinlogParamValues):
            self.headArray[index] = self.runModelForParams(param)
            self.fuzzyParam[index] = self.get_fuzzy(self.headArray[index])
            print(str(index+1)+'/'+str(self.FinlogParamValues.shape[0]),end='\r')
        np.save(self.sitefolder+'FinlogParamValues',self.FinlogParamValues)
        np.save(self.sitefolder+'FinheadArray',self.headArray)
        np.save(self.sitefolder+'FinfuzzyParam',self.fuzzyParam)
        self.state = 'end'
        """
    
    def get_fuzzy(self, head):
        '''
        E : Fuzzy Parameter (1-|Ap-Am|/Am)*(1-Si/Sm)*(1-Ni/Nm)
        Am : Total mesured saturated area 
        Ap : Total predicted saturated area 
        Sm : Number of mesured saturated pixels 
        Si : Number of incorrectly predicted saturated pixels
        Nm : Number of mesured non-saturated pixels
        Ni : Number of incorrectly predicted non-saturated pixels
        '''
        st()
        if np.isnan(np.sum(head))==True:
            paramList = [-9999,-9999,-9999,-9999,-9999,-9999,-9999,-9999]
        else:
            Am_array = (self.structure.hydro_network == 4) & (self.structure.watershed == 1)
            Am = np.sum(Am_array)
            Ap_array = head>=self.structure.dem
            Ap_array[self.bas.ibound.array[0] == -1] = False
            Ap_array[self.structure.watershed != 1] = False
            Ap = np.sum(Ap_array)
            Sm = Am.copy()
            kernel = np.ones((5, 5), dtype = int)
            Am_neightbours = convolve(Am_array, kernel, mode='constant')
            Si_array = np.zeros(Ap_array.shape)
            Si_array[(Ap_array==True) & (Am_neightbours== 0) & (self.structure.watershed == 1)] = 1
            Si= np.sum(Si_array)
            Nm_array = np.invert(self.structure.hydro_network == 4)
            Nm_array[self.structure.watershed != 1] = False
            Nm = np.sum(Nm_array)
            Ni_array = np.zeros(Ap_array.shape)
            Ni_array[(Ap_array==False) & (self.structure.hydro_network == 4)& (self.structure.watershed == 1)] = 1
            Ni = np.sum(Ni_array)
            Ea = 1-(np.abs(Ap-Am)/Am)
            E = Ea*(1-(Si/Sm))*(1-(Ni/Nm))
            paramList = [E,Ea,Ap,Am,Si,Sm,Ni,Nm]
        return paramList
        
    def runModelForParams(self,logParamValue):
        self.mf = flopy.modflow.Modflow(self.modelname, exe_name=self.filename+'mfnwt.exe', version='mfnwt',listunit=2, verbose=False, model_ws=self.modelfolder)
        self.nwt = flopy.modflow.ModflowNwt(self.mf, headtol=0.001, fluxtol=500, maxiterout=1000, thickfact=1e-05, linmeth=1,iprnwt=0,ibotav=0, options='COMPLEX')
        
        number_cells = np.arange(start=0, stop=self.structure.dem.shape[0] * self.structure.dem.shape[1])
        nb_cells = number_cells.reshape(self.structure.dem.shape[0], self.structure.dem.shape[1])

        file = pd.read_csv(self.filename+"data/input_file.txt", delimiter="\t", header=0)
        input_file = file.T.values

        nper = 1
        perlen = 1
        nstp = [1]
        steady = True

        # model domain and grid definition
        ztop = self.structure.dem
        delr = self.structure.geot[1]
        delc = abs(self.structure.geot[5])
        xul=self.structure.dem_x[0]
        yul=self.structure.dem_y[0]
        nlay = 1
        nrow = self.structure.dem.shape[0]
        ncol = self.structure.dem.shape[1]
        thick = 50
        thick_lay = thick / nlay
        zbot = np.ones((nlay, nrow, ncol))
        for i in range (1,nlay+1):
            zbot[i-1] = ztop - (thick_lay*i)

        # create discretization object
        self.dis = flopy.modflow.ModflowDis(self.mf, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=zbot, itmuni=4, lenuni=2,
        nper=nper, perlen=perlen, nstp=nstp, steady=steady, xul=xul,yul=yul,proj4_str='EPSG:2154')

        # variable for the BAS package
        iboundData = np.ones((nlay, nrow, ncol))
        #iboundData[0][demData == 0] = -1
        for i in range (0, nlay):
            iboundData[i][self.structure.dem <= self.structure.mean_sea_level] = -1
        #iboundData[0][sea_earth == 1] = 1
        strtData = np.ones((nlay, nrow, ncol))* ztop
        strtData[iboundData == -1] = self.structure.mean_sea_level

        self.bas = flopy.modflow.ModflowBas(self.mf, ibound=iboundData, strt=strtData, hnoflo=-9999)

        # lpf package
        laywet = np.zeros(nlay)
        laytype = np.ones(nlay)
        
        self.hk = np.ones((nlay, nrow, ncol))
        for i in range(0,len(self.number_structure)):
            for j in range(0,nlay):
                self.hk[j][self.structure.geology==self.number_structure[i]]= logParamValue[i]*3600*24
        
        Sy =0.1
        self.upw = flopy.modflow.ModflowUpw(self.mf, iphdry=1, hdry=-100, laytyp=laytype, laywet=laywet, hk=self.hk,
                                       vka=1, sy=Sy, noparcheck=False, extension='upw', unitnumber=31)

        rchData = {}
        for kper in range(0, nper):
            rchData[kper] = 0.001 #à Modifer avec surfex
        self.rch = flopy.modflow.ModflowRch(self. mf, rech=rchData)

        # Drain package (DRN)
        drnData = np.zeros((nrow*ncol, 5))
        drn_i = 0
        drnData[:, 0] = 0 # layer
        for i in range (0,nrow):
            for j in range (0, ncol):
                drnData[drn_i, 1] = i #row
                drnData[drn_i, 2] = j #col
                drnData[drn_i, 3]= ztop[i, j]#elev
                drnData[drn_i, 4] =self.hk[0, i, j]*delr * delc  #cond() 
                drn_i += 1
        lrcec= {0:drnData}
        self.drn = flopy.modflow.ModflowDrn(self.mf, stress_period_data=lrcec)
        
        # streamflow routing package
        #self.sfr2 = flopy.modflow.ModflowSfr2(self.mf,nss=2, nparseg=1)
        #self.str = flopy.modflow.ModflowStr(self.mf)
        #swr = flopy.modflow.ModflowSwr1(self.mf)
        
        # oc package
        stress_period_data = {}
        for kper in range(nper):
            kstp = nstp[kper]
            stress_period_data[(kper, kstp-1)] = ['save head','save budget',]
        self.oc = flopy.modflow.ModflowOc(self.mf, stress_period_data=stress_period_data, extension=['oc','hds','cbc'],
                                unitnumber=[14, 51, 52, 53, 0], compact=True)
        self.oc.reset_budgetunit(fname= self.modelname+'.cbc')

        # write input files
        self.mf.write_input()
        # run model
        succes, buff = self.mf.run_model(silent=True)
        if succes==True:
            hds = fpu.HeadFile(self.modelfolder+ '/' + self.modelname +'.hds')
            heads = hds.get_alldata()
            head = get_head(heads)
            self.extract_river_network_dem(head,str(logParamValue[0])+'_'+str(logParamValue[1])+'.tif')
        else:
            head = np.zeros([self.structure.dem.shape[0],self.structure.dem.shape[1]])*np.nan
        return head
        
    def display_Fuzzy(self):
        allParams = np.concatenate([self.ParamValues,self.FinParamValues])
        allFuzzy = np.concatenate([self.fuzzy,self.Finfuzzy])
        #allFuzzy[:,0][allFuzzy[:,0]<0] = 0
        #allFuzzy[:,0][allFuzzy[:,0]>2] = 2
        #allFuzzy[:,0:2][allFuzzy[:,1]<0.70] = 0
        Si_Sm = 1-(allFuzzy[:,4]/allFuzzy[:,3])
        #Si_Sm[Si_Sm<0]=0
        Ni_Nm = 1-(allFuzzy[:,6]/allFuzzy[:,3])
        
        normi = mpl.colors.Normalize(vmin=0, vmax=2);
        fig, ax = plt.subplots(figsize=(20,4), ncols=4)
        for i in range (0, ax.shape[0]):
            if i == 0 or 1: #E and Ea
                im = ax[i].tricontourf(allParams[:,0], allParams[:,1], allFuzzy[:,i], cmap='jet', levels=np.linspace(0,1,22))
                cl = ax[i].tricontour(allParams[:,0], allParams[:,1], allFuzzy[:,i], levels=[1],colors='k', linestyles='--')
            if i == 2:
                im = ax[i].tricontourf(allParams[:,0], allParams[:,1], Si_Sm , cmap='jet', levels=np.linspace(0,1,22),)
                cl = ax[i].tricontour(allParams[:,0], allParams[:,1], Si_Sm, levels=[1],colors='k', linestyles='--')
            if i == 3:
                im = ax[i].tricontourf(allParams[:,0], allParams[:,1], Ni_Nm, cmap='jet', levels=np.linspace(0,1,22),)
                cl = ax[i].tricontour(allParams[:,0], allParams[:,1], Ni_Nm, levels=[1],colors='k', linestyles='--')
                #plt.plot(allParams[:,0], allParams[:,1],'+')
            colbar = fig.colorbar(im, ax=ax[i], norm=normi)
        #colbar.norm = normi
            ax[i,].set_xscale('log')
            ax[i].set_yscale('log')
            #ax[i].set_xlim((1e-5,1e-2))
            #ax[i].set_ylim((6e-6,1e-3))
        plt.show()
            
def get_head(heads, axis=0):
    heads[0][heads[0]==-100]=np.nan
    if axis != 0:
        heads[0] = np.moveaxis(heads[0], axis, 0)
    mask = np.isnan(heads[0])
    idx = tuple(np.ogrid[tuple(map(slice, heads[0].shape[1:]))])
    res = heads[0][(np.argsort(mask, axis=0, kind='mergesort'),) + idx]
    head = res if axis == 0 else np.moveaxis(res, 0, axis)
    return head[0]

def figure(array):
    plt.figure(figsize=(10,10))
    plt.imshow(array)
    plt.colorbar()
    plt.show()