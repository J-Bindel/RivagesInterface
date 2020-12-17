# coding:utf-8
import math
import flopy
from flopy.export import vtk as fv
import os
import sys
import flopy.utils.binaryfile as fpu
import numpy as np
import pandas as pd
from osgeo import gdal
import get_geological_structure as ggs
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm

HK = 0 #homogeneous:1 & hétérogéneous:0
demPath = "dem.tif"

if os.path.exists(demPath):
    print("setting up MODFLOW simulation")
    modelname = "model1"
    mf1 = flopy.modflow.Modflow(modelname, exe_name='mfnwt.exe', version='mfnwt', verbose=True)
    nwt = flopy.modflow.ModflowNwt(mf1, headtol=0.0001, fluxtol=500, maxiterout=100, thickfact=1e-05, linmeth=1, iprnwt=0,
                               ibotav=0, options='COMPLEX')
    geot, geotx,geoty,demData, lay_wt, lay_ft, lay_kb, lay_kf, lay_kw = ggs()
    demData[demData == -99999.0] = 0
    print("DEM Load")

    #stats = demDs.GetRasterBand(1).GetStatistics(0, 1)

    number_cells = np.arange(start=0,stop=demData.shape[0]*demData.shape[1])
    nb_cells = number_cells.reshape(demData.shape[0], demData.shape[1])

    file = pd.read_table("input_file.txt", delimiter="\t", header=0)
    input_file = file.T.values
    a=np.mean(input_file[4,:])
    print("Rasters created")

    # Time step parameters
    nper = input_file.shape[1] # Number of model stress periods (the default is 1)
    perlen = input_file[1, :] # An array of the stress period lengths.
    nstp = input_file[2, :] # Number of time steps on each stress period (default is 1)
    nstp.astype(int)
    steady = input_file[3, :] == 1 # True : Study state | False : Transient state

    # model domain and grid definition
    ztop = demData
    ztop[demData == -99999.0] = 100
    nlay = 6
    nrow = demData.shape[0]
    ncol = demData.shape[1]
    H=100
    lay_wt[lay_wt == 0] = 20
    lay_ft[lay_ft == 0] = 20
    zbot = np.ones((nlay, nrow, ncol))
    lay_wz = lay_wt/(nlay/3)
    for i in range (0,int(nlay/3)):
        for j in range (0,nrow):
            for k in range (0,ncol):
                zbot[i, j, k] = ztop[j, k] - (lay_wz[j,k]* (1 + i))
    lay_fz = lay_ft / (nlay / 3)
    for i in range(0, int(nlay / 3)):
        for j in range(0, nrow):
            for k in range(0, ncol):
                zbot[i + int(nlay / 3), j, k] = ztop[j, k] - lay_wt[j, k] - (lay_fz[j, k] * (1 + i))
    lay_bz = (H - lay_wt - lay_ft) / (nlay/3)
    lay_bz[lay_wt == 0] = 0
    for i in range (0, int(nlay/3)):
        for j in range (0,nrow):
            for k in range (0,ncol):
                zbot[i+int(nlay/3)*2,j,k]=ztop[j,k]-lay_wt[j,k]- lay_ft[j,k]-(lay_bz[j,k]*(1 + i))
    delr = geot[1]
    delc = abs(geot[5])
    xul=geotx[0]
    yul=geoty[0]
    print("Domain created")

    zbot[5] = np.min(zbot[5])

    # create discretization object
    dis = flopy.modflow.ModflowDis(mf1, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=zbot, itmuni=4, lenuni=2,
    nper=nper, perlen=perlen, nstp=nstp, steady=steady,xul=xul,yul=yul,proj4_str='EPSG:2154')
    print("Discretization created")

    # variable for the BAS package
    iboundData = np.ones((nlay, nrow, ncol))
    iboundData[0][demData == 0] = -1
    iboundData[0][demData <= input_file[5, 0]] = -1
    for i in range (1,nlay):
        iboundData[i][demData == 0] = 0
        iboundData[i][demData <= input_file[5, 0]] = 0


    #ibndDs.GetRasterBand(1).WriteArray(iboundData[0])
    strtData = np.ones((nlay, nrow, ncol)) * ztop
    strtData[iboundData == -1] = input_file[5, 0]

    bas = flopy.modflow.ModflowBas(mf1, ibound=iboundData, strt=strtData, hnoflo=input_file[5, 0])
    print("BAS package created")



    # SWI2 Sea Water Intrusion
    khb = (0.0000000000256 * 1000. * 9.81 / 0.001) * 60 * 60 * 24
    kvb = (0.0000000000100 * 1000. * 9.81 / 0.001) * 60 * 60 * 24
    ssz = np.ones((nlay, nrow, ncol), np.float)
    ssz = 0.25*ssz
    z = np.ones((nlay,nrow,ncol), np.float)
    for i in range (0, nrow):
        a = np.linspace(0.63,-100,ncol)
        z[:,i,:]= a
    z[iboundData == -1] = 0
    isource = np.ones((nlay, nrow, ncol), np.int)
    for i in range (0, nlay):
        isource[i][iboundData[0] == -1] = 2

    solver2params = {'mxiter': 100, 'iter1': 20, 'npcond': 1, 'zclose': 1.0e-6,'rclose': 3e-3, 'relax': 1.0, 'nbpol': 2,
                     'damp': 1.0, 'dampt': 1.0}
    swi = flopy.modflow.ModflowSwi2(mf1, nsrf=1, iswizt=55, istrat=1, toeslope=0.025, tipslope=0.025, nu=[0, 0.025],
                                    zeta=z, ssz=ssz,isource=isource, nsolver=2,solver2params=solver2params)

    # lpf package
    laywet = np.zeros(nlay)
    laytype = np.ones(nlay)
    hk = np.ones((nlay, nrow, ncol))
    lay_kw[demData == 0] = 0.1
    if HK == 1:
        hk[:,:,:] = 0.864
    if HK == 0:
        hk[0, :, :] = lay_kw * (60 * 60 * 24)
        hk[1, :, :] = lay_kw * (60 * 60 * 24)
        hk[2, :, :] = lay_kf * (60 * 60 * 24)
        hk[3, :, :] = lay_kf * (60 * 60 * 24)
        hk[4, :, :] = lay_kb * (60 * 60 * 24)
        hk[5, :, :] = lay_kb * (60 * 60 * 24)


    #lpf = flopy.modflow.ModflowLpf(mf1, hk=0.864)
    upw = flopy.modflow.ModflowUpw(mf1, iphdry=1, hdry=-1e+30, laytyp=laytype, laywet=laywet, hk=hk, layvka=0,
                                   vka=hk,ss=1e-05, sy=ssz, noparcheck=False, extension='upw', unitnumber=31)
    print("LPF package created")
    # Recharge package (RCH)
    #rchData = np.ones(demData.shape, dtype=np.float32)
    #rchData = rechData*0.005
    rchData = {}
    for kper in range(0, nper):
        rchData[kper] = input_file[4, kper]
    rch = flopy.modflow.ModflowRch(mf1, rech=rchData)

    # Drain package (DRN)
    drnData = np.zeros((demData.shape[0]*demData.shape[1], 5))
    drnData[:, 0] = 0 # layer
    lrcec = {}
    for i in range(0, demData.shape[0]*demData.shape[1]):
        a = np.where(nb_cells == i)
        drnData[i, 1] = a[0] #row
        drnData[i, 2] = a[1] #col
        drnData[i, 3]= ztop[a[0], a[1]]#elev
        drnData[:, 4] = (hk[0, a[0], a[1]]) * delr * delc / 1  #cond
    for kper in range (0, nper):
        lrcec[kper] = drnData
    drn = flopy.modflow.ModflowDrn(mf1, stress_period_data=lrcec)

    # oc package
    stress_period_data = {}
    for kper in range(nper):
        kstp = nstp[kper]
        stress_period_data[(kper, kstp-1)] = ['save head',
                                            'save drawdown',
                                            'save budget',
                                            'save  ibound',
                                            'save head',
                                            'print head',
                                            'print budget']
    oc = flopy.modflow.ModflowOc(mf1, stress_period_data=stress_period_data, extension=['oc','hds','ddn','cbc','ibo'],
                                unitnumber=[14, 51, 52, 53, 0], compact=True)
    oc.reset_budgetunit(fname= modelname+'.cbc')

    #oc = flopy.modflow.ModflowOc(mf1, stress_period_data=stress_period_data, compact=True, chedfm='(10(1X1PE13.5))')
    #pcg = flopy.modflow.ModflowPcg (mf1, mxiter=500, hclose=1e-1, rclose=1e-1)
    print("OC package created")
    # write input files
    mf1.write_input()
    print("Input files wrote")
    # run model
    succes, buff = mf1.run_model()


