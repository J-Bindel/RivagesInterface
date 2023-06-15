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

from ipyleaflet import Map, GeoData, LayersControl, WidgetControl
from ipywidgets import HTML, Layout, Dropdown, VBox, Label, widgets, GridspecLayout, Button
from IPython.display import clear_output
import pandas as pd
import geopandas as gpd
import interface as interface
import simulation.settings_model as model
from src.custom_utils import helpers as utils

# Global variables


# /!\/!\ FOR THE CONTROL PANEL, SEE DOWN BELOW /!\/!\

header = HTML("<h1>Paramétrage du modèle</h1>", layout=Layout(height='auto'))
header.style.text_align='center'

map = Map(center=[49.3, -1.2333], zoom=10)
map_html = HTML('''Glissez le curseur sur le bassin versant pour afficher le code''')
gdf = gpd.read_file('../data/Hydro_net/ZONE_HYDROGRAPHIQUE_COTIER.shp',crs="EPSG:4326")

## Selectors

### Model name 
text_selector = widgets.Text(value='Nom du modèle', description='Nom : ')

### Site selector
sites_df = pd.read_table('../simulation/data/study_sites.txt', sep=',', index_col=1)
site_label = Label("Nom du site : ")
site_selector = Dropdown(options=sites_df.sites, layout=Layout(width='auto'))

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
simulation_state_1_1 = 'Le modèle est en cours de simulation...'
simulation_state_1_2 = 'Cela peut prendre plusieurs minutes/heures...'
simulation_state_1_3 = 'Veuillez patienter...'
simulation_state_2 = 'La simulation s\'est terminée normalement.'
simulation_state_3 = 'Les fichiers suivants ont été créés :'
simulation_state_4 = 'La simulation a rencontré un problème.'

# Functions
def region_name_and_code(feature, **kwargs):
        if feature is None: 
             wording = 'Glissez le curseur sur le bassin versant pour afficher le code'
             code = ""
        else:
            wording = feature['properties']['LIBELLE']
            code = feature['properties']['CODE_ZONE']
        map_html.value = '''
        <h4><b>{}</b></h4>
        <p>Code de la zone à modéliser: {}</p> 
        '''.format(wording, code)
        map_html.layout.height = '100px'
        map_html.layout.width = '540px'

def update_code_site(feature, **kwargs):
        site_selector.value=feature['properties']['CODE_ZONE']
        print("feature", feature['properties']['CODE_ZONE'])

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
        site_number = sites_df[sites_df.sites == site_selector.value].index[0]
        state = launch_simu(model_name, site_number, rate)


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
## Only one parameter is needed: the rate of the simulation    
def launch_simu(model_name, site_number, rate):
    model.setting(model_name, 32.27, 0, 0, 10.1, None, None, None, 0, 0, float(rate), None, None, site_number)
    state = 'end'
    return state

## Main function
def simulation_interface():

    map.add(LayersControl())
    map.layout.height='600px'
    map.layout.width='auto'
    map.layout.height='auto'

    map_html.layout.margin = '0px 20px 20px 20px'

    gdf_wgs = gdf.to_crs(epsg=4326)


    geo_data = GeoData(geo_dataframe = gdf_wgs,
                        style={'color': 'black', 'opacity':1, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0},
                        hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
                        name = 'Bassin Versants')
    
    map.add(geo_data)

    control = WidgetControl(widget=map_html, position='topright')
    map.add(control)
    
    geo_data.on_hover(region_name_and_code)
    geo_data.on_click(update_code_site)
                
    simulation_button.on_click(simulation_click)


    grid = GridspecLayout(3, 3, height='800px')
    grid[0:2, 0:2] = map
    grid[0:2, 2] = VBox([header, text_selector, site_label, site_selector, simulation_type_label, model_type_selector, date_selector_label, calendar_start, calendar_end, simulation_frequency_label, rate_selector])
    
    grid[2, 0:2] = VBox([simulation_button, simulation_output, simulation_files_output])
    return grid

control_panel = simulation_interface()