import os
import pandas as pd
import geopandas as gdp
from shapely.geometry import Polygon

# Global variables
sites_GPS = pd.read_table(os.path.dirname(os.path.abspath(__file__)) + "/../../simulation/data/study_sites_GPS.txt", sep=',', index_col=1)

def polygon_of_coordinates():
    """
    Function to create a geo_dataframe of the sites
    """
    study_sites = gdp.GeoDataFrame(columns=['sites', 'number', 'geometry', 'port'])
    for index, row in sites_GPS.iterrows():
        # Creating the polygon
        polygon = Polygon([(row['long_min'], row['lat_min']), (row['long_min'], row['lat_max']), (row['long_max'], row['lat_max']), (row['long_max'], row['lat_min'])])
        # Print the port number
        # Adding the polygon to the dataframe
        study_sites.loc[len(study_sites)] = {'sites': row['sites'], 'number': index, 'geometry': polygon, 'port': row['port_number']}

    # Saving the dataframe
    study_sites.to_file(os.path.dirname(os.path.abspath(__file__)) + "/../../simulation/data/study_sites.gpkg", layer="sites", driver="GPKG")

polygon_of_coordinates()  
