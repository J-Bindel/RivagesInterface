# coding:utf-8
import math
import flopy
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from osgeo import gdal
import get_geological_structure as ggs
from IPython.core.debugger import set_trace as st


def model_modflow(site_number,filename, modelname, modelfolder, coord, tdis, geo, permea, thick, port,porosity):
    mf1 = flopy.modflow.Modflow(modelname, exe_name=filename+'mfnwt.exe', version='mfnwt',listunit=2, verbose=False, model_ws=modelfolder)
    nwt = flopy.modflow.ModflowNwt(mf1, headtol=0.001, fluxtol=500, maxiterout=1000, thickfact=1e-05, linmeth=1,
                                   iprnwt=0,ibotav=0, options='COMPLEX')

    structure = ggs.structure(coord)
    geot = structure.geot
    geotx = structure.dem_x
    geoty = structure.dem_y
    demData = structure.dem
    river = structure.river
    st()
    '''
    r_dem='C:/Users/gauvain/Dropbox/HP_Article/Data/Versant_equivalent/DEMf.tif'
    dem = gdal.Open(r_dem)
    demData = dem.GetRasterBand(1).ReadAsArray()
    '''
    #ggs.save_clip_dem(site_number)
    demData[demData == -99999.0] = 0

    number_cells = np.arange(start=0, stop=demData.shape[0] * demData.shape[1])
    nb_cells = number_cells.reshape(demData.shape[0], demData.shape[1])

    file = pd.read_csv(filename+"data/input_file.txt", delimiter="\t", header=0)
    ram = pd.read_csv(filename+"data/RAM.csv", delimiter=";", header=0)
    sea_level = ram.NM_IGN[port-1]
    input_file = file.T.values

    if tdis == 0:
        # Time step parameters
        nper = input_file.shape[1]  # Number of model stress periods (the default is 1)
        perlen = input_file[1, :]  # An array of the stress period lengths.
        nstp = input_file[2, :]  # Number of time steps on each stress period (default is 1)
        nstp.astype(int)
        steady = input_file[3, :] == 1  # True : Study state | False : Transient state
    if tdis == 1 or tdis == 2 or tdis == 3:
        nper = 1
        perlen = 1
        nstp = [1]
        steady = True
    if tdis == 4:
        nper = 7
        perlen = 1
        nstp = [1,1,1,1,1,1,1]
        steady = [True,True,True,True,True,True,True]
    if tdis not in [0,1,2,3,4]:
        nper = 1
        perlen = 1
        nstp = [1]
        steady = True

    # model domain and grid definition
    ztop = demData
    ztop[demData == -99999.0] = 100
    delr = geot[1]
    delc = abs(geot[5])
    xul=geotx[0]
    yul=geoty[0]
    nlay = 6
    nrow = demData.shape[0]
    ncol = demData.shape[1]
    H=100
    zbot = np.ones((nlay, nrow, ncol))
    if geo == 1:
        lay_wt[lay_wt == 0] = 20
        lay_ft[lay_ft == 0] = 20
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


    if thick == 0 :
        zbot[0] = ztop - 20
        zbot[1] = ztop - 40
        zbot[2] = ztop - 60
        zbot[3] = ztop - 80
        zbot[4] = ztop - 100
        zbot[5] = np.min(zbot[4]) - 20

    if thick == 1:
        botm = np.min(ztop)-1
        thickness = ztop - botm
        thick_lay = thickness/nlay
        for i in range (1, nlay+1):
            zbot[i-1] = ztop - (thick_lay*i)

    if thick not in [0,1]:
        thickness = thick
        thick_lay = thickness / nlay
        for i in range (1,nlay+1):
            zbot[i-1] = ztop - (thick_lay*i)


    # create discretization object
    dis = flopy.modflow.ModflowDis(mf1, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=zbot, itmuni=4, lenuni=2,
    nper=nper, perlen=perlen, nstp=nstp, steady=steady, xul=xul,yul=yul,proj4_str='EPSG:2154')

    # variable for the BAS package
    iboundData = np.ones((nlay, nrow, ncol))
    #iboundData[0][demData == 0] = -1
    for i in range (0, nlay):
        iboundData[i][demData <= sea_level] = -1
    #iboundData[0][sea_earth == 1] = 1

    strtData = np.ones((nlay, nrow, ncol))* ztop
    strtData[iboundData == -1] = sea_level

    bas = flopy.modflow.ModflowBas(mf1, ibound=iboundData, strt=strtData, hnoflo=-9999)

    # lpf package
    laywet = np.zeros(nlay)
    laytype = np.ones(nlay)
    hk = np.ones((nlay, nrow, ncol))
    if geo == 0:
        hk[0, :, :] = permea
        hk[1, :, :] = permea
        hk[2, :, :] = permea
        hk[3, :, :] = permea
        hk[4, :, :] = permea
        hk[5, :, :] = permea
    if geo == 1:
        lay_kw[demData == 0] = 0.1
        hk[0, :, :] = lay_kw * (60 * 60 * 24)
        hk[1, :, :] = lay_kw * (60 * 60 * 24)
        hk[2, :, :] = lay_kf * (60 * 60 * 24)
        hk[3, :, :] = lay_kf * (60 * 60 * 24)
        hk[4, :, :] = lay_kb * (60 * 60 * 24)
        hk[5, :, :] = lay_kb * (60 * 60 * 24)

    upw = flopy.modflow.ModflowUpw(mf1, iphdry=1, hdry=-100, laytyp=laytype, laywet=laywet, hk=hk,
                                   vka=1, sy=porosity, noparcheck=False, extension='upw', unitnumber=31)

    rchData = {}
    if tdis == 0:
        input_file[4,0] = np.mean(input_file[4,:])
        for kper in range(0, nper):
            rchData[kper] = float(input_file[4, kper])
    if tdis == 1:
        for kper in range(0, nper):
            rchData[kper] = np.mean(input_file[4, :])
    if tdis == 2:
        for kper in range(0, nper):
            rchData[kper] = np.min(input_file[4, :])

    if tdis == 3:
        for kper in range(0, nper):
            rchData[kper] = np.max(input_file[4, :])

    if tdis == 4:
        rchData[0] = np.mean(input_file[4, :]) / 6
        rchData[1] = np.mean(input_file[4, :]) / 4
        rchData[2] = np.mean(input_file[4, :]) / 2
        rchData[3] = np.mean(input_file[4, :])
        rchData[4] = np.mean(input_file[4, :]) * 2
        rchData[5] = np.mean(input_file[4, :]) * 4
        rchData[6] = np.mean(input_file[4, :]) * 6

    if tdis not in [0, 1, 2, 3,4]:
        for kper in range(0, nper):
            rchData[kper] = tdis


    rch = flopy.modflow.ModflowRch(mf1, rech=rchData)

    # Drain package (DRN)
    drnData = np.zeros((nrow*ncol, 5))
    drn_i = 0
    drnData[:, 0] = 0 # layer
    for i in range (0,nrow):
        for j in range (0, ncol):
            drnData[drn_i, 1] = i #row
            drnData[drn_i, 2] = j #col
            drnData[drn_i, 3]= ztop[i, j]#elev
            drnData[drn_i, 4] =(hk[0, i, j]) * delr * delc / 1  #cond
            drn_i += 1
    lrcec= {0:drnData}
    drn = flopy.modflow.ModflowDrn(mf1, stress_period_data=lrcec)

    # oc package
    stress_period_data = {}
    for kper in range(nper):
        kstp = nstp[kper]
        stress_period_data[(kper, kstp-1)] = ['save head',
                                            'save budget',]
    oc = flopy.modflow.ModflowOc(mf1, stress_period_data=stress_period_data, extension=['oc','hds','cbc'],
                                unitnumber=[14, 51, 52, 53, 0], compact=True)
    oc.reset_budgetunit(fname= modelname+'.cbc')

    # write input files
    mf1.write_input()
    # run model
    succes, buff = mf1.run_model()

