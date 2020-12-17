# coding:utf-8
import os
import pandas as pd
import threading
from model_modflow import model_modflow as modflow
from model_modpath import model_modpath as modpath
from model_seawat import model_seawat as seawat
from vtk_export_grid import vtk_export_grid as vtk_grid
from vtk_export_watertable import vtk_export_watertable as vtk_watertable
from vtk_export_pathlines import vtk_export_pathlines as vtk_pathlines

########################################################################################################################
#                                                      MODEL SETTINGS                                                  #
########################################################################################################################

# FOLDER
filename = r'H:/Users/gauvain/DEM/'

# STUDY SITES
sites = pd.read_csv("study_sites.txt", sep='\s+', header=0, index_col=0)

site_number = [1] #Select site number
permeability = [0.864]
theta = [0.01]
geology = [0]
time = [0.001]
thick = [50]


def setting(site_number,permeability, time, geology, theta, thick):
    coordinates = sites._get_values[site_number,1:5]
    # TIME DISCRETIZATION
    time_param = time  # 0: chronicle | 1: mean (1 day Steady State) | 2: min (1 day SS) | 3: max (1 day SS) | 4: 7 periods (R/4 R/2 R 2R 4R 6R 8R) | or values of recharge (1 SS)

    # STRUCTURE
    geology_param = geology  # 0: homogeneous geology | 1: heterogeneous geology
    permeability_param = permeability  # m/d | only if geology_param = 0
    theta_param = theta # Porosity in %
    thickness_param = thick  # 0: homogeneous thickness | 1: flat bottom (heterogeneous thickness) | or values of thicknesse

    # MODEL NAME
    site_name = sites.index._data[site_number] + '/'
    model_name = r'model_' + 'time_' + str(time_param) + '_geo_' + str(geology_param) + '_thick_' + str(thickness_param)
    if geology_param == 0:
        model_name = model_name + '_K_' + str(permeability_param) + '_Sy_' + str(theta_param)
    model_folder = model_name + '/'

    # SIMULATION
    modflow_param = 0 # 0: disabled | 1: enabled
    seawat_param = 0  # 0: disabled | 1: enabled
    if time ==4 or time==1 or time not in [0,1,2,3,4]:
        modpath_param= 1  # 0: disabled | 1: enabled
    else:
        modpath_param = 0
        # VTK OUTPUT
    grid = 0 # 0: disabled | 1: enabled
    watertable = 0 # 0: disabled | 1: enabled
    pathlines = 0 # 0: disabled | 1: enabled

    # CREATE AND RUN MODFLOW MODEL - SEAWAT MODEL - MODPATH MODEL
    if modflow_param == 1:
        modflow(site_number=site_number,filename=filename, modelname=model_name, modelfolder=filename + site_name + model_folder,
                coord=coordinates, tdis=time_param, geo=geology_param,
                permea=permeability_param, thick=thickness_param, port=int(sites._get_values[site_number,5]), porosity=theta_param)
    if seawat_param == 1:
        seawat(filename=filename,modelfolder=filename + site_name + model_folder, modelname=model_name)
    if modpath_param == 1:
        modpath(filename=filename, modelname=model_name, modelfolder=filename + site_name + model_folder)

    # CREATE OUTPUT FILES
    if not os.path.exists(filename + site_name + model_folder + 'output_files'):
        os.makedirs(filename + site_name + model_folder + 'output_files')
    if grid == 1:
        vtk_grid(modelname=model_name, modelfolder=filename + site_name + model_folder, coord=coordinates)
    if watertable == 1:
        vtk_watertable(modelname=model_name, modelfolder=filename + site_name + model_folder, coord=coordinates)
    if pathlines == 1:
        vtk_pathlines(modelname=model_name, modelfolder=filename + site_name + model_folder, coord=coordinates)

