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
import get_geological_structure as ggs

########################################################################################################################
#                                                      MODEL SETTINGS                                                  #
########################################################################################################################

# FOLDER
filename = r'H:/Users/gauvain/DEM/'

# STUDY SITES
sites = pd.read_csv("study_sites_exutoires.txt", sep='\s+', header=0, index_col=0)

site_number = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30] #Select site number

def setting(site_number,test):
    ggs.save_clip_dem(site_number)

compt=0
coeur=35
for sim in range (0, len(site_number)):
    compt += 1
    t = threading.Thread(target=setting, args=(site_number[sim],0))
    t.start()
    if int(compt / coeur) == compt / coeur:  # Si compt est multiple de 3
        t.join()  # alors on attend que les modèles soient terminées pour recommencer
        print(compt)
t.join() # On attend que les modèles soient finis pour terminer le calcul
