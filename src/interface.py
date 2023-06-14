# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 20:20:00 2020

@author: Alexandre Gauvain
"""

"""
Interface Rivages tool
"""

from ipyleaflet import Map, basemaps, basemap_to_tiles, Heatmap, TileLayer,GeoData, LayersControl,WidgetControl
from ipywidgets import HTML, Layout, Dropdown, Output, Textarea, VBox, Label, widgets,AppLayout,GridspecLayout, Button
from IPython.display import display, Markdown, clear_output
import numpy as np
import geopandas as gpd
from pandas import date_range
import src.interface as interface
import src.model_modflow_calibration as mmc
import simulation.settings_model as model
from simulation.custom_utils import helpers as utils

def affichage_carte():
    m = Map(center=[49, -1], zoom=10)
    gdf = gpd.read_file('data/Hydro_net/ZONE_HYDROGRAPHIQUE_COTIER.shp',crs="EPSG:4326")
    gdf_wgs = gdf.to_crs(epsg=4326)
    geo_data = GeoData(geo_dataframe = gdf_wgs,
                        style={'color': 'black', 'opacity':1, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0},
                        hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
                        name = 'Bassin Versants')
    '''surfex_data = GeoData(geo_dataframe = surfex_wgs,
                        style={'color': 'blue', 'opacity':1, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0},
                        hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
                        name = 'Maillage SURFEX')
    m.add_layer(surfex_data)'''
    m.add_layer(geo_data)
    html = HTML('''Glissez le curseur sur le bassin versant pour afficher le code''')
    html.layout.margin = '0px 20px 20px 20px'
    control = WidgetControl(widget=html, position='topright')
    m.add_control(control)
    
    def update_html(feature, **kwargs):
        html.value = '''
        <h3><b>{}</b></h3>
        <h4>Code de la zone à modéliser: {}</h4> 
        '''.format(feature['properties']['LIBELLE'],
        feature['properties']['CODE_ZONE'])
    def update_CodeSite(feature, **kwargs):
        site_selector.value=feature['properties']['CODE_ZONE']
        print("feature", feature['properties']['CODE_ZONE'])
    geo_data.on_hover(update_html)
    geo_data.on_click(update_CodeSite)
    m.add_control(LayersControl())

    header = HTML("<h1>Parametrage du modèle</h1>", layout=Layout(height='auto'))
    header.style.text_align='center'
    site_selector = Dropdown(options=gdf.CODE_ZONE,
                                layout=Layout(width='auto'))
    modele_selector = Dropdown(options=('Transitoire', 'Permanent'),
                                layout=Layout(width='auto'))
    scenario_selector = Dropdown(options=('Actuel','RCP 2.6', 'RCP 4.5','RCP 6.0','RCP 8.5'),
                                layout=Layout(width='auto'))
    rate_selector = Dropdown(options=('1','7', '15','21', '30','45', '50', '60', '75', '90', '100', '125', '150','182', '200','250', '300', '330', '365', '550', '640', '730', '1000','1500','2000','2250','3000','3182', '3652'),
                                 value="3652",
                                layout=Layout(width='auto'))
    text_selector = widgets.Text(
           value='Nom du modèle',
           description='NOM:', )
    slider = widgets.IntSlider(
             value=1,
             min=1,
             max=90,
             step=1)

    calendar_start = widgets.DatePicker(
               description='Début')
    calendar_end = widgets.DatePicker(
               description='Fin')

    m.layout.height='600px'
    m.layout.width='auto'
    m.layout.height='auto'

    def create_expanded_button(description, button_style):
        return Button(description=description, button_style=button_style, layout=Layout(height='auto', width='auto'))
    
    button = Button(description='Lancer la simulation', button_style='info', layout=Layout(height='auto', width='auto'))
    but_calib = Button(description='Lancer la calibaration', button_style='info', layout=Layout(height='auto', width='auto'))
    
    out = widgets.Output()
    
    out_info_files_simu = widgets.Output()
    
    def on_button_clicked(_):
        button.disabled=True
        with out:
            # what happens when we press the button
            clear_output()
            print('Le modèle est en cours de simulation...')
            print('Cela peut prendre plusieurs minutes/heures...')
            display(HTML('''<i style="text-align:center" class="fa fa-circle-notch fa-spin fa-3x fa-fw"></i>
<span class="sr-only">Loading...</span>'''))
            
        #state = test_xy(slider) ### Pour miner l'attente processing
        rate = rate_selector.value
        state = launch_simu(rate)
        if state == 'end':
            button.disabled=False
            with out:
                clear_output()
                print("La simulation s'est terminée normalement.")
                display(HTML('''<i style="text-align:center" class="fa fa-check-square fa-3x fa-fw"></i>
                <span class="sr-only"></span>'''))
            with out_info_files_simu:
                clear_output()
                print("La simulation s'est terminée normalement.")
                model_name = utils.generate_model_name(0, 0, float(rate_selector.value), None, None, site=3, permeability_param=32.27)
                print("The following files have been created:")
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
                
        if state != 'end':
            button.disabled=False
            with out:
                clear_output()
                print("La simulation a rencontré un problème.")
                display(HTML('''<i class="fa fa-times fa-3x fa-fw"></i>
                <span class="sr-only"></span>'''))
                
    out_calib = widgets.Output()
    def on_button_clicked_calib(_):
        but_calib.disabled=True
        with out_calib:
            # what happens when we press the button
            clear_output()
            print('La calibration est en cours de réalisation...')
            print('Cela peut prendre plusieurs minutes/heures...')
            display(HTML('''<i style="text-align:center" class="fa fa-circle-notch fa-spin fa-3x fa-fw"></i>
<span class="sr-only">Loading...</span>'''))
        calib = mmc.calibration(site_selector.value,out_calib)
        calib.run_calibration()
        if calib.state == 'end':
            but_calib.disabled=False
            with out_calib:
                clear_output()
                print("La calibration s'est terminée normalement.")
                display(HTML('''<i style="text-align:center" class="fa fa-check-square fa-3x fa-fw"></i>
                <span class="sr-only"></span>'''))   
        if calib.state != 'end':
            but_calib.disabled=False
            with out_calib:
                clear_output()
                print("La calibration a rencontré un problème.")
                display(HTML('''<i class="fa fa-times fa-3x fa-fw"></i>
                <span class="sr-only"></span>'''))
                
    button.on_click(on_button_clicked)
    but_calib.on_click(on_button_clicked_calib)

    grid = GridspecLayout(4, 4, height='800px')
    grid[:, 1:3] = m
    grid[:, 0] = VBox([text_selector,Label("CODE DU SITE:"), site_selector, Label("SIMULATION:"), modele_selector, Label("Si Transitoire:"), calendar_start, calendar_end,Label('Discrétisation temporelle (en jours):') ,slider, Label("SCENARIO:"), scenario_selector,Label("RATE:"), rate_selector,])
    
    grid[:, 3] = VBox([button,out,but_calib,out_calib, out_info_files_simu])

    return grid,text_selector, site_selector,modele_selector, calendar_start, calendar_end, slider, scenario_selector, button

def test_xy(site_selector):
    for i in range (0,100000000):
        a=1
    state = 'end'
    return state
    
def launch_simu(rate):
    model.setting(32.27, 0, 0, 10.1, None, None, None, 0, 0, float(rate), None, None, site=3)
    state = 'end'
    return state
    