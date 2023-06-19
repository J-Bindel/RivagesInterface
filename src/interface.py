# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 20:20:00 2020

@author: Alexandre Gauvain
"""

"""
Interface Rivages tool
"""

import sys
sys.path.append('../')

from ipyleaflet import (
    Map, Marker, TileLayer, ImageOverlay, Polyline, Circle, CircleMarker, Rectangle, GeoJSON, DrawControl,
    GeoData, LayersControl, WidgetControl
)
from ipywidgets import HTML, Layout, Dropdown, VBox, Label, widgets, GridspecLayout, Button
from IPython.display import clear_output
import pandas as pd
import geopandas as gpd
import interface as interface
import simulation.settings_model as model
from src.custom_utils import helpers as utils
from src.custom_utils import find_biggest_city as fbc

# Global variables

## Model parameters
permability = 32.27
theta = 10.1
geology = 0
thickness = 1
time = 0
ref = None
chronicle = 0
approx = 0
rep = None
steady = None
input_file = None
modflow_enabled = 1
seawat_enabled = 0
grid = 0
watertable = 0
pathlines = 0

# /!\/!\ FOR THE CONTROL PANEL, SEE DOWN BELOW /!\/!\

header = HTML("<h1 style=\"text-align: center;\">Paramétrage du modèle</h1><br>", layout=Layout(height='auto'))

map = Map(center=[49.3, -1.2333], zoom=10)
map_html = HTML('''Glissez le curseur sur le bassin versant pour afficher le code''')
rect_color = '#A52A2A'
myDrawControl = DrawControl(rectangle={'shapeOptions':{'color': rect_color}})

## Selectors

### Model name 
text_selector = widgets.Text(value='Nom du modèle', description='Nom : ')

### Site selector
coordinates_label = Label("Les coordonnées courantes du site sont : ")
instructions_label = Label("Veuillez dessiner un rectangle sur la carte pour les actualiser.")
vertice_ll = Label("0.0")
vertice_ul = Label("0.0")
vertice_ur = Label("0.0")
vertice_lr = Label("0.0")
city_label = Label()

### Model selector
simulation_type_label = Label("Type de simulation:")
model_type_selector = Dropdown(options=('Transitoire', 'Permanent'), layout=Layout(width='auto'))

### Date selector
date_selector_label = Label("Si Transitoire, veuillez-choisir une date :")
calendar_start = widgets.DatePicker(description='Début')
calendar_end = widgets.DatePicker(description='Fin')

### Scenario selector
scenario = ['Actuel','RCP 2.6', 'RCP 4.5','RCP 6.0','RCP 8.5']
scenario_selector = Dropdown(options=(scenario), layout=Layout(width='auto'))

### Rate selector
simulation_frequency_label = Label('Fréquence de simulation (en jours) :')
rate = ['15','21', '30','45', '50', '60', '75', '90', '100', '125', '150','182', '200','250', '300', '330', '365', '550', '640', '730', '1000','1500','2000','2250','3000','3182', '3652']
rate_selector = Dropdown(options=(rate), value="3652", layout=Layout(width='auto'))


## Buttons
simulation_button = Button(description='Lancer la simulation', button_style='info', layout=Layout(height='auto', width='auto'))

## Outputs
simulation_output = widgets.Output()
simulation_files_output = widgets.Output()

## Simulation state
## Used in the simulation click function
simulation_state_1_1 = 'Le modèle est en cours de simulation...'
simulation_state_1_2 = 'Cela peut prendre plusieurs minutes/heures...'
simulation_state_1_3 = 'Veuillez patienter...'
simulation_state_2 = 'La simulation s\'est terminée normalement.'
simulation_state_3 = 'Les fichiers suivants ont été créés :'
simulation_state_4 = 'La simulation a rencontré un problème.'

# Functions

def clear_map():
    global rect
    rect = tuple((0.0, 0.0, 0.0, 0.0))

def handle_draw(self, action, geo_json):
    global rect
    clear_map()
    polygon=[]
    for coords in geo_json['geometry']['coordinates'][0][:-1][:]:
        polygon.append(tuple(coords))
    polygon=tuple(polygon)
    if action == 'created':
        rect = polygon
        update_coordinates_label()
        update_city_label()

def update_coordinates_label():
    """
    Update the coordinates label with the coordinates of the current rectangle
    ll means lower left, ul means upper left, ur means upper right, lr means lower right
    """
    ll_x = "{:.2f}".format(rect[0][0])
    ll_y = "{:.2f}".format(rect[0][1])
    ul_x = "{:.2f}".format(rect[1][0])
    ul_y = "{:.2f}".format(rect[1][1])
    ur_x = "{:.2f}".format(rect[2][0])
    ur_y = "{:.2f}".format(rect[2][1])
    lr_x = "{:.2f}".format(rect[3][0])
    lr_y = "{:.2f}".format(rect[3][1])
    vertice_ll.value = "    - Coin inférieur gauche : "+ll_x+", "+ll_y
    vertice_ul.value = "    - Coin supérieur gauche : "+ul_x+", "+ul_y
    vertice_ur.value = "    - Coin supérieur droit : "+ur_x+", "+ur_y
    vertice_lr.value = "    - Coin inférieur droit : "+lr_x+", "+lr_y

def update_city_label():    
    """
    Update the city label with the name of the biggest city included 
    in the current rectangle
    """
    ll_x = rect[0][0]
    ll_y = rect[0][1]
    ur_x = rect[2][0]
    ur_y = rect[2][1]
    city = fbc.find_biggest_city(ll_x, ll_y, ur_x, ur_y)
    city_label.value = "Le site sélectionné est : "+city


## Function to add an event on the simulation button
def simulation_click(_):
        simulation_button.disabled=True
        with simulation_output:

            # what happens when we press the button
            clear_output()
            print(simulation_state_1_1)
            print(simulation_state_1_2)
            print(simulation_state_1_3)
    
        # Launch simulation
        rate = rate_selector.value
        model_name = text_selector.value
        #site_number = sites_df[sites_df.sites == site_selector.value].index[0]

        state = launch_simu(model_name, 2, permability, theta, geology, thickness, time, ref, chronicle, approx, rate, rep, steady, input_file, modflow_enabled, seawat_enabled, grid, watertable, pathlines)


        if state == 'end':
            simulation_button.disabled=False
            with simulation_output:
                clear_output()
                print(simulation_state_2)
            with simulation_files_output:
                clear_output()
                print(simulation_state_3)
                simulation_file_produced()
                
        else:
            simulation_button.disabled=False
            with simulation_output:
                clear_output()
                print(simulation_state_4)

## Auxiliary function to print the files produced by the simulation
def simulation_file_produced(): 
    model_name = text_selector.value + "_"
    model_name += utils.generate_model_name(0, 0, float(rate_selector.value), None, None, site=3, permeability_param=32.27)
    print(model_name + ".bas")
    print(model_name + ".dis")
    print(model_name + ".drn")
    print(model_name + ".hds")
    print(model_name + ".list")
    print(model_name + ".nam")
    print(model_name + ".nwt")
    print(model_name + ".oc")
    print(model_name + ".rch")
    print(model_name + ".upw")

## Function to run a simulation    
def launch_simu(model_name, site_number, permability, theta, geology, thickness, time, ref, chronicle, approx, rate, rep, steady, input_file, modflow_enabled, seawat_enabled, grid, watertable, pathlines):
    model.setting(model_name, site_number, permability, theta, geology, thickness, time, ref, chronicle, approx, rate, rep, steady, input_file, modflow_enabled, seawat_enabled, grid, watertable, pathlines)
    state = 'end'
    return state

## Main function
def simulation_interface():

    map.add(LayersControl())
    map.layout.height='600px'
    map.layout.width='auto'
    map.layout.height='auto'

    map_html.layout.margin = '0px 20px 20px 20px'

    myDrawControl.on_draw(handle_draw)
    map.add(myDrawControl)

    control = WidgetControl(widget=map_html, position='topright')
    map.add(control)
                
    simulation_button.on_click(simulation_click)


    # Creating a grid of 4 rows and 4 columns
    grid = GridspecLayout(4, 4, height='1200px')

    ## The first two columns are used to display the map
    grid[0:3, 0:2] = map

    ## The third and the fourth columns are used to display the control panel

    ### The first two row and last two columns are used to display the header, the model name selector, the model type and the date selector
    grid[0:2, 2:4] = VBox([header, text_selector, simulation_type_label, model_type_selector, date_selector_label, calendar_start, calendar_end, simulation_frequency_label, rate_selector])
                        

    ### The third row is used to display the coordinates label and the city label
    grid[2, 2:4] = VBox([coordinates_label, instructions_label, vertice_ll, vertice_ul, vertice_ur, vertice_lr, city_label])
    
    ### Finally, the last row is used to display the simulation button and the simulation output
    grid[3, :] = VBox([simulation_button, simulation_output, simulation_files_output])

    return grid

# An other global variable
## Used to display the generate the control panel 
##    in the Jupyter notebook
control_panel = simulation_interface()