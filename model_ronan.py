# coding:utf-8
import os
import flopy
import flopy.utils.binaryfile as fpu
import numpy as np


def model(K):
    modelname = 'model'+str(K)
    modelfolder = 'H:/Users/gauvain/G2H/model_ronan/'
    mf1 = flopy.modflow.Modflow(modelname, exe_name='mfnwt.exe', version='mfnwt', verbose=True, model_ws=modelfolder)
    # nwt
    nwt = flopy.modflow.ModflowNwt(mf1, headtol=0.01, fluxtol=500, maxiterout=1000, thickfact=1e-05, linmeth=1,
                                   iprnwt=0, ibotav=0, options='COMPLEX')
    # Modflow 2005 => Package PCG

    nrow = 50
    ncol = 100
    nlay = 10
    # nlay*nrow*ncol < 2000000 cells

    delr = 5
    delc = 5
    top = np.ones((nrow, ncol))
    slope = 0.05
    x = np.linspace(1, 100, 100)
    for i in range(0, nrow):
        top[i, :] = x*delr * slope

    botm = np.ones((nlay, nrow, ncol))
    for i in range(0, nlay):
        botm[i] = top - (2 * (i + 1))

    # Time step parameters
    nper = 1  # Number of model stress periods (the default is 1)
    perlen = np.ones(nper)  # An array of the stress period lengths.
    nstp = np.ones(nper)  # Number of time steps on each stress period (default is 1)
    steady = np.ones(nper) * True  # True : Study state | False : Transient state

    # create discretization object
    dis = flopy.modflow.ModflowDis(mf1, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm,
                                   itmuni=4, lenuni=2, nper=nper, perlen=perlen, nstp=nstp, steady=steady)
    laytyp = np.ones(nlay)  # 1 convertible, confined
    laywet = np.zeros(nlay)  #
    hk = np.ones(nlay) * K  # m/d
    phi = np.ones(nlay) * 0.10
    upw = flopy.modflow.ModflowUpw(mf1, hdry=-100, laytyp=laytyp, laywet=laywet, hk=hk, layvka=0,
                                   vka=1, noparcheck=False, extension='upw', unitnumber=31, sy=phi)
    # Modflow2005 -> Package lpf

    iboundData = np.ones((nlay, nrow, ncol))
    iboundData[0, :, 0] = -1
    strtData = np.ones((nlay, nrow, ncol)) * top
    bas = flopy.modflow.ModflowBas(mf1, ibound=iboundData, strt=strtData, hnoflo=-9999.0)

    # Recharge package (RCH)
    rchData = np.ones((nrow, ncol)) * 0.002  # m/d
    rch = flopy.modflow.mfrch.ModflowRch(mf1, rech=rchData)

    # Drainage package (DRN)
    drnData = np.zeros((nrow * (ncol), 5))
    drnData[:, 0] = 0  # layer
    compt = 0
    for i in range(0, nrow):
        for j in range(0, ncol):
            drnData[compt, 1] = i  # row
            drnData[compt, 2] = j  # col
            drnData[compt, 3] = top[i, j]  # elev
            drnData[compt, 4] = hk[0] * delr * delc  # (K) * delr * delc / 1  # cond
            compt +=  1
    lrcec = {0: drnData}
    drn = flopy.modflow.ModflowDrn(mf1, stress_period_data=lrcec, options=['NOPRINT'])

    # oc package
    stress_period_data = {}
    for kper in range(nper):
        kstp = nstp[kper]
        stress_period_data[(kper, kstp - 1)] = ['save head', 'save budget']
    oc = flopy.modflow.ModflowOc(mf1, stress_period_data={(0, 0): ['save head', 'save budget']},
                                 extension=['oc', 'hds', 'ddn', 'cbc'],
                                 unitnumber=[14, 51, 52, 53], compact=True);
    oc.reset_budgetunit(fname=modelname + '.cbc')
    # pcg = flopy.modflow.ModflowPcg (mf1, mxiter=100000)

    # write input files
    mf1.write_input()
    # run model
    succes, buff = mf1.run_model()

    if succes == True:
        dis_file = '{}.dis'.format(mf1.name)
        head_file = '{}.hds'.format(mf1.name)
        bud_file = '{}.cbc'.format(mf1.name)

        mp1 = flopy.modpath.Modpath(modelname=mf1.name + '_flowlines', simfile_ext='mpsim', namefile_ext='mpnam',
                                    version='modpath',
                                    exe_name='mp6.exe', modflowmodel=mf1, dis_file=dis_file, dis_unit=87,
                                    head_file=head_file, budget_file=bud_file, model_ws=modelfolder)
        mp1.array_free_format = True

        cbb = fpu.CellBudgetFile(modelfolder + '{}.cbc'.format(mf1.name))
        # cbb.list_records()
        rec = cbb.get_data(kstpkper=(0, 0), text='FLOW LOWER FACE')

        szone = []
        for i in range(0, nlay):
            a = np.zeros((nrow, ncol), dtype=int)
            if i == 0:
                a[rec[0][0] < 0] = 1
            szone.append(a)

        sim = flopy.modpath.ModpathSim(model=mp1, option_flags=[2, 1, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1],
                                       group_placement=[[1, 1, 1, 0, 1, 1]], stop_zone=1, zone=szone)
        stl = flopy.modpath.mpsim.StartingLocationsFile(model=mp1, inputstyle=1)

        hds_1c = fpu.HeadFile(modelfolder + '{}.hds'.format(mf1.name))
        head_1c = hds_1c.get_alldata(mflay=None, nodata=-1e30)

        stldata = flopy.modpath.mpsim.StartingLocationsFile.get_empty_starting_locations_data(npt=ncol*nrow)

        compt = 0
        for i in range(0, nrow):
            for j in range(0, ncol):
                stldata[compt]['label'] = 'p' + str(compt + 1)
                for k in range(0, nlay):
                    if (head_1c[0][k, i, j] > dis.botm.array[k,i, j]):
                        stldata[compt]['k0'] = k+1
                        break
                stldata[compt]['j0'] = j
                stldata[compt]['i0'] = i
                stldata[compt]['zloc0'] = 0.9
                compt = compt + 1
        stl.data = stldata
        mpbas = flopy.modpath.ModpathBas(mp1, hnoflo=-9999.0, hdry=-100, def_iface=[6, 6], def_face_ct=2, laytyp=laytyp,
                                         ibound=iboundData, prsity=phi, prsityCB=phi, extension='mpbas', unitnumber=86,
                                         bud_label=['DRAINS', 'CONSTANT HEAD'])

        mp1.write_input()
        cwd = os.path.join(os.getcwd(), modelname)
        mpsf = '{}.mpsim'.format(modelfolder + mf1.name)
        mp_exe_name = 'mp6.exe'
        xstr = '{} {}'.format(mp_exe_name, mpsf)
        succes, buff = mp1.run_model()


K1 = [86.4]
for i in range (0, len(K1)):
    K=K1[i]
    model(K)