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
import interface
import model_modflow_calibration as mmc

def affichage_carte():
    m = Map(center=[49, -1], zoom=10)
    gdf = gpd.read_file('C:/Users/alexa/Dropbox/PhD/4 - Data/ZONE_HYDROGRAPHIQUE_FXX-shp/ZONE_HYDROGRAPHIQUE_COTIER.shp',crs="EPSG:4326")
    #surfex =gpd.read_file('C:/Users/alexa/Dropbox/Dev/Hdf_extract/DATA/maille_meteo_fr_pr93.shp',crs="EPSG:4326")
    gdf_wgs = gdf.to_crs(epsg=4326)
    #surfex_wgs = surfex.to_crs(epsg=4326)
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
    geo_data.on_hover(update_html)
    m.add_control(LayersControl())

    header = HTML("<h1>Parametrage du modèle</h1>", layout=Layout(height='auto'))
    header.style.text_align='center'
    site_selector = Dropdown(options=gdf.CODE_ZONE,
                                layout=Layout(width='auto'))
    modele_selector = Dropdown(options=('Transitoire', 'Permanent'),
                                layout=Layout(width='auto'))
    scenario_selector = Dropdown(options=('Actuel','RCP 2.6', 'RCP 4.5','RCP 6.0','RCP 8.5'),
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
    def on_button_clicked(_):
        button.disabled=True
        with out:
            # what happens when we press the button
            clear_output()
            print('Le modèle est en cours de simulation...')
            print('Cela peut prendre plusieurs minutes/heures...')
            display(HTML('''<i class="fa fa-circle-notch fa-spin fa-3x fa-fw"></i>
<span class="sr-only">Loading...</span>'''))
        state = test_xy(slider)
        if state == 'end':
            button.disabled=False
            with out:
                clear_output()
                print("La simulation s'est terminé normalement.")
                display(HTML('''<i class="fa fa-check-square fa-3x fa-fw"></i>
                <span class="sr-only"></span>'''))   
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
            display(HTML('''<i class="fa fa-circle-notch fa-spin fa-3x fa-fw"></i>
<span class="sr-only">Loading...</span>'''))
        calib = mmc.calibration(site_selector.value,out_calib)
        calib.run_calibration()
        if calib.state == 'end':
            but_calib.disabled=False
            with out_calib:
                clear_output()
                print("La calibration s'est terminé normalement.")
                display(HTML('''<i class="fa fa-check-square fa-3x fa-fw"></i>
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
    grid[:, 0] = VBox([text_selector,Label("CODE DU SITE:"), site_selector, Label("SIMULATION:"), modele_selector, Label("Si Transitoire:"), calendar_start, calendar_end,Label('Discrétisation temporelle (en jours):') ,slider, Label("SCENARIO:"), scenario_selector,])
    
    grid[:, 3] = VBox([button,out,but_calib,out_calib])

    return grid,text_selector, site_selector,modele_selector, calendar_start, calendar_end, slider, scenario_selector, button

def test_xy(site_selector):
    for i in range (0,100000000):
        a=1
    state = 'end'
    return state
    