import os 
import pandas as pd

# Global variables
data_path = os.path.dirname(os.path.abspath(__file__)) + "/../../data/simulation_sites/"

# Functions
def find_biggest_city(x_min, y_min, x_max, y_max):
    """
    Find the biggest city according to the pop_and_GPS.csv file

    Parameters
    ----------
    x_min : float
        The minimum latitude
    y_min : float
        The minimum longitude
    x_max : float
        The maximum latitude
    y_max : float
        The maximum longitude

    Returns
    -------
    str
        The name of the biggest city
    """
    # Reading the file 
    df = pd.read_csv(data_path+"pop_and_GPS.csv", sep=",")

    # Filtering the dataframe
    df = df[(df['longitude'] >= x_min) & (df['longitude'] <= x_max) & (df['latitude'] >= y_min) & (df['latitude'] <= y_max)]
    df = df.sort_values(by=['PTOT'], ascending=False)


    return df.iloc[0]['COM']