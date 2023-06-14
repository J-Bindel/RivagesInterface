"""
    Provides functions to compute flooded surface.
"""

import os
import numpy as np
import re
import argparse
import sys
import flopy.utils.binaryfile as fpu
import math
import csv
import pandas as pd
import math
import flopy
import pickle
import statistics
#from utils import utils as u

__author__ = "June Sallou"
__maintainer__ = "June Sallou"
__credits__ = ["June Sallou"]
__license__ = "MIT"
__version__ = "0.0.4"
__date__ = "07/02/2019"
__email__ = "june.benvegnu-sallou@univ-rennes1.fr"


mainAppRepo = os.path.dirname(os.path.abspath(__file__)) + '/'

dc = 0.3  # depth of threshold for the undeground vulnerable zone
alpha = float(1/3)

def get_soil_surface_values_for_a_simulation(repo_simu, model_name):
    """
        Retrieve the matrix of the topographical altitude.
    """
    mf = flopy.modflow.Modflow.load(repo_simu + "/" + model_name + '.nam')
    dis = flopy.modflow.ModflowDis.load(
        repo_simu + "/" + model_name + '.dis', mf)
    topo = dis.top._array
    
    return topo

def get_model_name(site_number, chronicle, approx, rate, ref, perm):
    model_name = "model_time_0_geo_0_thick_1_K_86.4_Sy_0.1_Step1_site" + str(site_number) + "_Chronicle" + str(chronicle)
    if perm:
        model_name += "_SteadyState"
    elif not ref:
        model_name += "_Approx" + str(approx)
        if approx == 0:
            model_name += "_Period" + str(rate)
        elif approx==1:
            model_name += "_RechThreshold" + str(rate)
    return model_name

def get_site_name_from_site_number(site_number):
    sites = pd.read_csv(mainAppRepo + 'data/study_sites.txt',
                        sep=',', header=0, index_col=0) #\\s+
    site_name = sites.index._data[site_number] + '/'
    return site_name

def get_path_to_simulation_directory(site_number, chronicle, approx, rate, ref, perm):
    model_name = get_model_name(site_number, chronicle, approx, rate, ref, perm)
    site_name = get_site_name_from_site_number(site_number)
    return os.path.join(mainAppRepo, "outputs/", site_name, model_name)

def getNonDryCellHdsValue(hds, nrow, ncol, nlayer):
    layer = 0
    h = hds[layer][nrow][ncol]
    while (math.isclose(abs(h)/1e+30, 1, rel_tol=1e-3)) and layer < nlayer:
        if layer == nlayer-1:
            print("cell completely dry")
        else:
            h = hds[layer+1][nrow][ncol]
            layer += 1
    return h


def getWeightToSurface(zs, h, dc, alpha):
    """
        zs : value of soil surface at the point x
        h : head value for watertable at the x point
        dc : critical depth
        alpha : ratio of critical depth for calculating the width of transition zone
    """
    ddc = alpha * dc  # Alpha must be not null

    borneInf = zs - (dc + (ddc / 2))
    borneSup = zs - (dc - (ddc / 2))

    if h <= borneInf:
        Ws = 0
    elif h >= borneSup:
        Ws = 1
    else:
        Ws = math.sin((math.pi * (h - borneSup)) / (2*ddc))

    return Ws


def getSaturatedZoneArea(site_number, chronicle, folder, ref, dc, alpha, timestep=1):
    
    model_name = get_model_name(site_number, chronicle, None, None, ref, perm=True)

    if folder is None:
        repo_simu = get_path_to_simulation_directory(site_number, chronicle, None, None, ref=ref, perm=True)
    else :
        site_name = get_site_name_from_site_number(site_number)
        print(site_name)
        repo_simu = folder + site_name + model_name

    topoSimu = get_soil_surface_values_for_a_simulation(repo_simu, model_name)

    simuHds = fpu.HeadFile(repo_simu + '/' + model_name + '.hds')
    # simuTimes = simuHds.get_times()
    # simuKstpkper = simuHds.get_kstpkper()
    # print(simuTimes, simuKstpkper)
    hds_data = simuHds.get_data(kstpkper=(0,0))
    # print(hds_data)

    nbrowtot = hds_data.shape[1]        
    nbcoltot = hds_data.shape[2]

    size_site = nbrowtot * nbcoltot
    Ws_sum = 0
    saturated_area = 0

    for nrow in range(nbrowtot):
        for ncol in range(nbcoltot):

            Zs = topoSimu[nrow][ncol]
            h = getNonDryCellHdsValue(hds_data, nrow, ncol, hds_data.shape[0])
            d =  Zs - h
            if d<= dc:
                saturated_area += 1
            Ws_sum += getWeightToSurface(Zs, h, dc, alpha)
    


    with open(repo_simu + "/" + model_name + '_extracted_features.csv', 'w') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Satured Zone Area', 'Vulnerability Sum', 'Vulnerability Rate', 'Global Area of site (in cells)'])
        writer.writerow([saturated_area, Ws_sum, Ws_sum/size_site, size_site])
    print("Saturated Area : ", saturated_area)
    print("Vulnerability Sum : ", Ws_sum)
    print("Vulnerability Rate : ", Ws_sum/size_site)
    print("Global Area of site :", size_site)
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-site", "--sitenumber", type=int, required=True)
    parser.add_argument("-chr", "--chronicle", type=int, required=True)
    parser.add_argument("-approx", "--approximation", type=int, required=False)
    parser.add_argument("-rate", "--rate", type=float, required=False)
    parser.add_argument("-dc", "--criticaldepth", type=float, required=False)
    parser.add_argument("-alpha", "--alpha", type=float, required=False)
    parser.add_argument("-ref", "--ref", action='store_true')
    parser.add_argument("-f", "--folder", type=str, required=False)
    
    parser.add_argument("-ts", "--timestep", type=int, required=False)
    


    args = parser.parse_args()

    site_number = args.sitenumber
    timestep = args.timestep
    dc = args.criticaldepth
    alpha = args.alpha
    chronicle= args.chronicle
    approx=args.approximation
    rate = args.rate
    ref = args.ref
    folder = args.folder



    if timestep is None:
        timestep = 1
    
    if alpha is None:
        alpha = float(1/3)

    getSaturatedZoneArea(site_number, chronicle, folder, ref=False, dc=0.3, alpha=alpha, timestep=timestep)
