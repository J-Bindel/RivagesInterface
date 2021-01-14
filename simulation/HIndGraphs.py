import re
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import argparse

##### OUTDATED !! ######

##### Generating CSV File with indicators for all simulations #####

mainAppRepo = os.path.dirname(os.path.abspath(__file__)) + '/'

def get_model_name(site_number, chronicle, approx, rate, ref):
    model_name = "model_time_0_geo_0_thick_1_K_86.4_Sy_0.1_Step1_site" + str(site_number) + "_Chronicle" + str(chronicle)
    if not ref:
        model_name += "_Approx" + str(approx)
        if approx == 0:
            model_name += "_Period" + str(rate)
        elif approx==1:
            model_name += "_RechThreshold" + str(rate)
    return model_name

def get_site_name_from_site_number(site_number):
    sites = pd.read_csv(mainAppRepo + 'data/study_sites.txt',
                        sep=',', header=0, index_col=0) #\\s+
    site_name = sites.index._data[site_number]
    return site_name


def getExecutionTimeFromListFile(file):
    with open(file,'r') as f:
        lines = f.readlines()
        if lines:
            beforelast_line = lines[-2]
    beforelast_line=beforelast_line.rstrip()

    m = re.search(r'\sElapsed run time:\s+(?:(\d*)?(?:\sDays,\s*))?(?:(\d*)(?:\s*Hours,\s*))?(?:(\d*)(?:\s*Minutes,\s*))?(\d*[.]*\d*)\sSeconds', beforelast_line)
    if (m.group(1) is None) and (m.group(2) is None) and (m.group(3) is None):
        exec_time = float(m.group(4))
    elif (m.group(1) is None) and (m.group(2) is None):
        exec_time = int(m.group(3))*60 + float(m.group(4))      
    elif (m.group(1) is None):
        exec_time = int(m.group(2))*60*60 + int(m.group(3))*60 + float(m.group(4))
        print(m.group(2), m.group(3), m.group(4), exec_time)
    else:
        exec_time = int(m.group(1))*24*60*60 + int(m.group(2))*60*60 + int(m.group(3))*60 + float(m.group(4))
    return int(exec_time)


def get_number_of_lines_in_input_file(file):
    with open(file) as f:
        count = sum(1 for _ in f)
    return count

def createGlobalCSVFile(indicator, folder, site, chronicle, approx):
    """
    sitename : #Agon-Coutainville #Saint-Germain-Sur-Ay
    
    """
    site_name = get_site_name_from_site_number(site)
    ref_name = get_model_name(site, chronicle, None, None, ref=True)

    mainRepo = folder + site_name + '/'
    
    if approx == 0:
        approximations = [1.0, 2.0, 7.0, 30.0, 90.0, 182.0, 365.0, 730.0, 3652.0]
        nb_lines = [15341, 7671, 2193, 513, 172, 86, 44, 23, 6]
    else:
        approximations = [0, 0.0002, 0.05, 0.1, 0.2, 0.25, 0.4, 0.5, 0.8, 1.0, 2.0]
        nb_lines = [15341, 6597, 239, 122, 62, 50, 32, 26, 17, 14, 8]
    
    modelnames = [ref_name]
    for appr in range(1, len(approximations)):
         modelnames.append(get_model_name(site, chronicle, approx, approximations[appr], ref=False))

   
    dfglob = pd.DataFrame()

    for ind in range(len(modelnames)):
        simuRepo = modelnames[ind]
        if ind == 0:
            d = {'H Error': [0.0]}
            df = pd.DataFrame(data=d)
        else:
            filename = simuRepo + "_Ref_" + ref_name + "_errorsresult_" + indicator +"_light.csv"
            df = pd.read_csv(mainRepo + simuRepo + "/" + filename, sep=";")

    
        taille = len(df.index)
        df_dur = pd.DataFrame(data=[approximations[ind]]*taille, index=df.index, columns=['Approximation'])
        exec_time = getExecutionTimeFromListFile(mainRepo + simuRepo + "/" + simuRepo + ".list")
        df_time = pd.DataFrame(data=[exec_time]*taille, index=df.index, columns=['Execution Time'])
        df_lines = pd.DataFrame(data=[nb_lines[ind]]*taille, index=df.index, columns=['Number of Lines'])
        df = pd.concat([df, df_dur, df_time, df_lines], axis=1)
        dfglob = pd.concat([dfglob,df])

    output = "Exps_" + indicator + "_Indicator_" + site_name + "_Chronicle"+ str(chronicle) + "_Approx" + str(approx)

    dfglob.to_csv(mainRepo + output + ".csv")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-ind", "--indicator", type=str, required=True)
    parser.add_argument("-site", "--site", type=int, help= "2: Agon-Coutainville or 3:Saint-Germain-Sur-Ay", required=True)
    parser.add_argument("-approx", "--approximation", type=int, required=True)
    parser.add_argument("-chr", "--chronicle", type=int)
    parser.add_argument("-f", "--folder", type=str, required=True)
    args = parser.parse_args()
    
    site = args.site
    chronicle = args.chronicle
    outliers = True
    indicator = args.indicator
    folder= args.folder
    approx = args.approximation

    
    createGlobalCSVFile(indicator, folder, site, chronicle, approx)