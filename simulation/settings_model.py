# coding:utf-8


import os,sys
sys.path.append('../')

import pandas as pd
import argparse
from simulation.model_modflow import model_modflow as modflow
from simulation.model_modpath import model_modpath as modpath
from simulation.model_seawat import model_seawat as seawat
from simulation.vtk_export_grid import vtk_export_grid as vtk_grid
from simulation.vtk_export_watertable import vtk_export_watertable as vtk_watertable
from simulation.vtk_export_pathlines import vtk_export_pathlines as vtk_pathlines
from src.custom_utils import helpers as utils

# Global variables


folder_path = os.path.dirname(os.path.abspath(__file__)) + '/' 

sites = pd.read_table(folder_path + "data/study_sites.txt", sep=',', header=0, index_col=0) 

## Model parameters
permeability = [8.64] ###Ref = 86.4
theta = [0.1]  ###Porosity
geology = [0]
time = [0]

## Model information
information_1 = "Numéro du site : "
infromation_2 = "Nom du site : "

## Modflow information
modflow_information_1 = "Fichier : "
modflow_information_2 = "Chemin du dossier : "
modflow_information_3 = "Chemin vers le modèle : "


# Functions

## Main function
### @param model_name: name of the model
### @param permeability: permeability of the soil
    #### m²/d | only if geology = 0
### @param time: time discretization
    #### 0: chronicle | 1: mean (1 day Steady State) | 2: min (1 day SS) | 3: max (1 day SS)
### @param geology: geology of the soil
    #### 0: homogeneous geology | 1: heterogeneous geology
### @param theta: porosity of the soil
    #### Porosity in %
### @param input_file: input file
### @param step: step of the simulation
### @param ref: reference
### @param chronicle: chronicle
### @param approx: approximation
### @param rate: frequency of the simulation
### @param rep: repetition
### @param steady: steady state
### @param site_number: number of the site
### @param thickness: thickness of the soil
    #### 0: homogeneous thickness | 1: flat bottom (heterogeneous thickness)
def setting(model_name, permeability, time, geology, theta, input_file, step, ref, chronicle, approx, rate, rep, steady, site_number, thickness=1):

    # Site and coordinates
    site = sites.loc[sites['number']==site_number]
    site_name = sites.index._data[site_number]
    coordinates = [site.iloc[0]["xmin"], site.iloc[0]["xmax"], site.iloc[0]["ymin"], site.iloc[0]["ymax"]]
    

    
    print_model_info(site_number)

    site_path = site_name + '/'

    model_path = model_name + "_" + utils.generate_model_name(chronicle, approx, rate, ref, steady, site_number, permeability=permeability)

    if rep:
        model_path = model_path + "_" + str(rep)

    model_folder = model_path + '/'


    if input_file is None:
        if ref:
            chronicle_file = pd.read_table(folder_path + "data/chronicles.txt", sep=',', header=0, index_col=0)
            input_file = chronicle_file.template[chronicle]

        else:
            input_file = utils.get_input_file_name(chronicle, approx, rate, ref, steady, site_number=None, step=None)   
    
    # Simulation
    modflow_param = 1  # 0: disabled | 1: enabled
    seawat_param = 0  # 0: disabled | 1: enabled

    if time == 1:
        modpath_param = 1  # 0: disabled | 1: enabled
    else:
        modpath_param = 0

    # Vtk output
    grid = 0  # 0: disabled | 1: enabled
    watertable = 0  # 0: disabled | 1: enabled
    pathlines = 0 # 0: disabled | 1: enabled

    # Create and run Modflow model
    if modflow_param == 1:
        # Information about the model
        print_modflow_information(input_file, model_folder)

        # Run the model
        modflow(input_file, file_name=folder_path, model_name=model_path, model_folder=folder_path + "outputs/" + site_path + model_folder,
                coord=coordinates, tdis=time, geo=geology, permea=permeability, thick=thickness, port=int(site.iloc[0]["port_number"]), porosity=theta, ref=ref)
        
    # Create and run Seawat model
    if seawat_param == 1:
        seawat(filename=folder_path,modelfolder=folder_path + site_path + model_folder, modelname=model_path)

    # Create and run Modpath model
    if modpath_param == 1:
        modpath(filename=folder_path, modelname=model_path + '_swt', modelfolder=folder_path + site_path + model_folder)

    # Create output files
    if not os.path.exists(folder_path + "outputs/" + site_path + model_folder + 'output_files'):
        os.makedirs(folder_path+ "outputs/" + site_path + model_folder + 'output_files')

    
    if grid == 1:
        vtk_grid(modelname=model_path, modelfolder=folder_path + "outputs/" + site_path + model_folder, coord=coordinates)
    if watertable == 1:
        vtk_watertable(modelname=model_path, modelfolder=folder_path + "outputs/" + site_path + model_folder, coord=coordinates)
    if pathlines == 1:
        vtk_pathlines(modelname=model_path + '_swt', modelfolder=folder_path + "outputs/" + site_path + model_folder, coord=coordinates)

def print_model_info(site_number):
    print(information_1, site_number)
    print(infromation_2, sites.index._data[site_number])
    print(folder_path)

def print_modflow_information(input_file, model_folder):
    print(modflow_information_1, input_file)
    print(modflow_information_2, folder_path)
    print(modflow_information_3, model_folder)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inputfile", type=str, required=False)
    parser.add_argument("-ts", "--timestep", type=int, required=False)
    parser.add_argument("-ref", "--reference", action='store_true')
    parser.add_argument("-chr", "--chronicle", type=int, required=True)
    parser.add_argument("-site", "--site", type=int, required=False)
    parser.add_argument("-rate", "--rate", type=float, required=False)
    parser.add_argument("-approx", '--approximation', type=int, required=False)
    parser.add_argument("-rep", '--rep', type=int, required=False)
    parser.add_argument("-perm", "--permeability", type=float, required=False)
    parser.add_argument("-sd", "--steady", type=int, required=False)
    args = parser.parse_args()

    input_file = args.inputfile
    step = args.timestep
    rate = args.rate
    reference = args.reference
    site=args.site
    chronicle = args.chronicle
    approx = args.approximation
    rep=args.rep
    perm = args.permeability
    steady=args.steady 

    if rep==0:
        rep=None

    if site:
        if perm:
            setting(perm, time[0], geology[0], theta[0], input_file, step, reference, chronicle, approx, rate, rep, steady, site=site)
        else:
            setting(permeability[0], time[0], geology[0], theta[0], input_file, step, reference, chronicle, approx, rate, rep, steady, site=site)
    else:
        if perm:
            setting(perm, time[0], geology[0], theta[0], input_file, step, reference, chronicle, approx, rate, rep, steady)
        else:
            setting(permeability[0], time[0], geology[0], theta[0], input_file, step, reference, chronicle, approx, rate, rep, steady)
