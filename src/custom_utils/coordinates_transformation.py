import os
import pandas as pd
from osgeo import gdal
from osgeo import osr

# Global variables

## Retrieve the using study sites
sites = pd.read_table(os.path.dirname(os.path.abspath(__file__)) + "/../../simulation/data/study_sites.txt", sep=',', index_col=1)
## Removing the Granville_Baneville site
sites = sites.drop(0)

## Retrieve the TIFF file
src = gdal.Open(os.path.dirname(os.path.abspath(__file__)) + "/../../simulation/data/MNT_TOPO_BATH_75m.tif")

# Functions
def get_transform_object():
    # Getting the spatial reference
    source = osr.SpatialReference()
    source.ImportFromWkt(src.GetProjection())

    # Getting the target spatial reference
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    
    # Creating the transform object
    return osr.CoordinateTransformation(source, target)

def convert_coordinates_to_lat_long(x, y):
    # Getting the transform object
    transform = get_transform_object()

    # Transforming the coordinates
    return transform.TransformPoint(x, y)

def convert_site_coordinate():
    sites_GPS = pd.DataFrame(columns=['sites', 'number', 'lat_min', 'long_min', 'lat_max', 'long_max', 'port_number'])
    for index, row in sites.iterrows():
        # Getting the coordinates
        lat_min, long_min, z = convert_coordinates_to_lat_long(row['xmin'], row['ymin'])
        lat_max, long_max, z = convert_coordinates_to_lat_long(row['xmax'], row['ymax'])

        # Adding the coordinates to the dataframe
        sites_GPS.loc[len(sites_GPS)]={'sites': row['sites'], 'number': index, 'lat_min': lat_min, 'long_min': long_min, 'lat_max': lat_max, 'long_max': long_max, 'port_number': row['port_number']}

    # Saving the dataframe
    sites_GPS.to_csv(os.path.dirname(os.path.abspath(__file__)) + "/../../simulation/data/study_sites_GPS.txt", sep=",", index=False)

convert_site_coordinate()