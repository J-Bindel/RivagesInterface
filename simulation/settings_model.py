# coding:utf-8


import os,sys
sys.path.append('../')

import pandas as pd
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
permeability = [8.64] ### Ref = 86.4
theta = [0.1]  ### Porosity
geology = [0]
time = [0]

## Model information
information_1 = "Numéro du site : "
infromation_2 = "Nom du site : "

## Modflow information
modflow_information_1 = "Fichier d'entrée : "
modflow_information_2 = "Chemin du dossier : "
modflow_information_3 = "Chemin vers le modèle : "


# Functions

def setting(model_name, site_number, permeability, theta, geology, thickness, time, ref, chronicle, approx, rate, rep, steady, input_file, modflow_enabled, seawat_enabled, grid, watertable, pathlines):

    """
    Main function

    Parameters
    ----------
    model_name : str
        Name of the model
    site_number : int
        Number of the site
    permeability : float
        Permeability of the soil
        m²/d | only if geology = 0
    theta : float
        Porosity of the soil in %
    geology : int
        Geology of the soil
        0: homogeneous geology | 1: heterogeneous geology
    thickness : int
        Thickness of the soil
        0: homogeneous thickness | 1: flat bottom (heterogeneous thickness)
    time : int
        Time discretization
        0: chronicle | 1: mean (1 day Steady State) | 2: min (1 day SS) | 3: max (1 day SS)
    ref : int
        Reference
    chronicle : int
        Chronicle
    approx : int
        Approximation
    rate : int
        Frequency of the simulation
    rep : int
        Repetition
    steady : int
        Steady state
    input_file : str
        Input file
    modflow_enabled : int  
        Modflow enabled 
        0: disabled | 1: enabled
    seawat_enabled : int
        Seawat enabled 
        0: disabled | 1: enabled
    grid : int
        Grid 
        0: disabled | 1: enabled
    watertable : int
        Watertable 
        0: disabled | 1: enabled
    pathlines : int
        Pathlines 
        0: disabled | 1: enabled
    """
    # Site and coordinates
    site = sites.loc[sites['number']==site_number]
    site_name = sites.index._data[site_number]
    site_path = site_name + '/'
    coordinates = [site.iloc[0]["xmin"], site.iloc[0]["xmax"], site.iloc[0]["ymin"], site.iloc[0]["ymax"]]
    

    
    print_model_info(site_number)

    # Model path and folder
    model_path = model_name + "_" + utils.generate_model_name(chronicle, approx, rate, ref, steady, site_number, permeability_param=permeability)
    if rep:
        model_path = model_path + "_" + str(rep)
    model_folder = model_path + '/'


    # Input file
    if input_file is None:
        if ref:
            chronicle_file = pd.read_table(folder_path + "data/chronicles.txt", sep=',', header=0, index_col=0)
            input_file = chronicle_file.template[chronicle]

        else:
            input_file = utils.get_input_file_name(chronicle, approx, rate, ref, steady, site=None, step=None)   
    

    # Modpath enabled ?
        # 0: disabled | 1: enabled
    if time == 1:
        modpath_enabled = 1  
    else:
        modpath_enabled = 0

    # Create and run Modflow model
    if modflow_enabled == 1:

        # Information about the model
        print_modflow_information(input_file, model_folder)

        # Run the model
        modflow(input_file, file_name=folder_path, model_name=model_path, model_folder=folder_path + "outputs/" + site_path + model_folder,
                coord=coordinates, tdis=time, geo=geology, permea=permeability, thick=thickness, port=int(site.iloc[0]["port_number"]), porosity=theta, ref=ref)
        
    # Create and run Seawat model
    if seawat_enabled == 1:
        seawat(filename=folder_path,modelfolder=folder_path + site_path + model_folder, modelname=model_path)

    # Create and run Modpath model
    if modpath_enabled == 1:
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

def print_modflow_information(input_file, model_folder):
    print(modflow_information_1, input_file)
    print(modflow_information_2, folder_path)
    print(modflow_information_3, model_folder)
