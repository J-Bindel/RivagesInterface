import os
import pandas as pd

# Global variables
data_path = os.path.dirname(os.path.abspath(__file__)) + "/../../data/simulation_sites/"

# Functions
def remove_useless_zeros():
    """
    Function to remove the useless zeros in the CODCOM column
    """
    df_with_pop_and_no_coordinates = pd.read_csv(data_path+"donnees_communes.csv", sep=";")
    df_with_pop_and_no_coordinates['CODCOM'] = df_with_pop_and_no_coordinates['CODCOM'].astype(str)
    df_with_pop_and_no_coordinates['CODCOM'] = df_with_pop_and_no_coordinates['CODCOM'].str.lstrip('0')
    df_with_pop_and_no_coordinates['CODCOM'] = df_with_pop_and_no_coordinates['CODCOM'].astype(int)
    df_with_pop_and_no_coordinates.to_csv(data_path+"donnees_communes.csv", sep=";", index=False)



def append_coordinate_columns():
    """
    Function to append the latitude and longitude columns of 
    """
    # First dataframe, with the population but no coordinates
    df_with_pop_and_no_coordinates = pd.read_csv(data_path+"donnees_communes.csv", sep=";")

    # Second dataframe, this time with the coordinates but no population
    cols_to_keep = ['latitude', 'longitude', 'code_commune', 'code_region']
    d_types = {'latitde': str, 'longitude': float, 'code_commune': str, 'code_region': str}
    df_with_no_pop_and_coordinates = pd.read_csv(data_path+"communes_GPS.csv", usecols=cols_to_keep, dtype=d_types)

    # Changing the type of the columns
    df_with_pop_and_no_coordinates['CODCOM'] = df_with_pop_and_no_coordinates['CODCOM'].astype(str)
    df_with_pop_and_no_coordinates['CODREG'] = df_with_pop_and_no_coordinates['CODREG'].astype(str)

    # Merging the two dataframes
    df_with_pop_and_no_coordinates = pd.merge(df_with_pop_and_no_coordinates, df_with_no_pop_and_coordinates, on=['CODCOM', 'CODREG'])

    df_with_pop_and_no_coordinates.to_csv(data_path+"pop_and_GPS.csv", sep=",", index=False)

append_coordinate_columns()