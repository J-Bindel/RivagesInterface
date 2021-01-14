import re
import os
import numpy as np
import pandas as pd
import argparse
import csv
from custom_utils import helpers as utils

##### Generating CSV File with indicators for all simulations #####

mainAppRepo = os.path.dirname(os.path.abspath(__file__)) + '/'

# def get_model_name(site_number, chronicle, approx, rate, ref):
#     model_name = "model_time_0_geo_0_thick_1_K_86.4_Sy_0.1_Step1_site" + str(site_number) + "_Chronicle" + str(chronicle)
#     if not ref:
#         model_name += "_Approx" + str(approx)
#         if approx == 0 or approx == 2:
#             model_name += "_Period" + str(rate)
#         elif approx==1:
#             model_name += "_RechThreshold" + str(rate)
#     return model_name


def getExecutionTimeFromListFile(file):
    with open(file,'r') as f:
        lines = f.readlines()
    if lines is not None:
        beforelast_line = lines[-2]
        beforelast_line=beforelast_line.rstrip()

    m = re.search(r'\sElapsed run time:\s+(?:(\d*)?(?:\sDays,\s*))?(?:(\d*)(?:\s*Hours,\s*))?(?:(\d*)(?:\s*Minutes,\s*))?(\d*[.]*\d*)\sSeconds', beforelast_line)
    if m is None:
        return -9
    if (m.group(1) is None) and (m.group(2) is None) and (m.group(3) is None):
        exec_time = float(m.group(4))
    elif (m.group(1) is None) and (m.group(2) is None):
        exec_time = int(m.group(3))*60 + float(m.group(4))      
    elif (m.group(1) is None):
        exec_time = int(m.group(2))*60*60 + int(m.group(3))*60 + float(m.group(4))
        #print(m.group(2), m.group(3), m.group(4), exec_time)
    else:
        exec_time = int(m.group(1))*24*60*60 + int(m.group(2))*60*60 + int(m.group(3))*60 + float(m.group(4))
    return int(exec_time)


def get_number_of_lines_in_input_file(file):
    with open(file) as f:
        count = sum(1 for _ in f)
    return count

def createGlobalCSVFile(indicator, folder, site, chronicle, approx, permeability, bve):
    """
    sitename : #Agon-Coutainville #Saint-Germain-Sur-Ay
    
    """
    site_name = utils.get_site_name_from_site_number(site)
    ref_name = utils.get_model_name(site, chronicle, None, None, ref=True, steady=False, permeability=permeability)

    mainRepo = folder + site_name + '/'
    
    if approx == 0 or approx == 2:
        approximations = [1.0, 2.0, 7.0, 15.0, 21.0, 30.0, 45.0, 50.0, 60.0, 75.0, 90.0, 100.0, 125.0, 150.0, 182.0, 200.0, 250.0, 300.0, 330.0, 365.0, 550.0, 640.0, 730.0, 1000.0, 1500.0, 2000.0, 2250.0, 3000.0, 3182.0, 3652.0]
        nb_lines = [0] * 30 # Fix: value not necessary! Or find the correct ones.
    else:
        approximations = [0, 0.0002, 0.05, 0.1, 0.2, 0.25, 0.4, 0.5, 0.8, 1.0, 2.0]
        nb_lines = [15341, 6597, 239, 122, 62, 50, 32, 26, 17, 14, 8]
    
    modelnames = [ref_name]
    for appr in range(1, len(approximations)):
         modelnames.append(utils.get_model_name(site, chronicle, approx, approximations[appr], ref=False, steady=False, permeability=permeability))

   
    dfglob = pd.DataFrame()

    for ind in range(len(modelnames)):
        simuRepo = modelnames[ind]
        if ind == 0:
            d = {'H Error': [0.0]}
            df = pd.DataFrame(data=d)
        else:
            if bve:
                filename = simuRepo + "_Ref_" + ref_name + "_errorsresult_" + indicator +"_BVE.csv"
            else:
                filename = simuRepo + "_Ref_" + ref_name + "_errorsresult_" + indicator +"_light.csv"
            try:
                df = pd.read_csv(mainRepo + simuRepo + "/" + filename, sep=";")
            except FileNotFoundError:
                print("File not Found: ", filename)
                continue

    
        taille = len(df.index)
        df_dur = pd.DataFrame(data=[approximations[ind]]*taille, index=df.index, columns=['Approximation'])
        #print(mainRepo + simuRepo + "/" + simuRepo + ".list")
        exec_time = getExecutionTimeFromListFile(mainRepo + simuRepo + "/" + simuRepo + ".list")
        if exec_time == -9:
            print("Time Execution Error for : ", simuRepo)
            continue
        df_time = pd.DataFrame(data=[exec_time]*taille, index=df.index, columns=['Execution Time'])
        df_lines = pd.DataFrame(data=[nb_lines[ind]]*taille, index=df.index, columns=['Number of Lines'])
        #df_geomorph = pd.read_csv("/DATA/These/OSUR/Extract_BV_june/" + str(site) + "_slope_elevation_Lc_Cw_A", sep=",")
        #print(df_geomorph)

        with open("/DATA/These/OSUR/Extract_BV_june/" + str(site) + "_slope_elevation_Lc_Cw_A", newline='') as f:
            reader = csv.reader(f)
            geomorph = list(reader)

        # with open(mainRepo + "Feature_CV_HV_Site_"+ str(site)+"_BVE.csv") as f_vul:
        #     readerv = csv.reader(f_vul)
        #     vulne = list(readerv)

        vulne = pd.read_csv(mainRepo + "Feature_CV_HV_Site_"+ str(site)+"_BVE.csv", sep=";")
        #print(vulne["Coastal Vulnerability"][0])
        #print(geomorph)
        df_slope = pd.DataFrame(data=[float(geomorph[0][0])]*taille, index=df.index, columns=['Slope'])
        df_elev = pd.DataFrame(data=[float(geomorph[0][1])]*taille, index=df.index, columns=['Elevation'])
        df_Lc = pd.DataFrame(data=[float(geomorph[0][2])]*taille, index=df.index, columns=['LC'])
        df_Cw = pd.DataFrame(data=[float(geomorph[0][3])]*taille, index=df.index, columns=['CW'])
        df_A = pd.DataFrame(data=[float(geomorph[0][4])]*taille, index=df.index, columns=['Area'])
        df_CV =pd.DataFrame(data=[float(vulne["Coastal Vulnerability"][0])]*taille, index=df.index, columns=['CV'])
        df_HV =pd.DataFrame(data=[float(vulne["Hydrological Vulnerability"][0])]*taille, index=df.index, columns=['HV'])
        df = pd.concat([df, df_dur, df_time, df_lines, df_slope, df_elev, df_Lc, df_Cw, df_A, df_CV, df_HV], axis=1)
        dfglob = pd.concat([dfglob,df])

    output = "Exps_" + indicator + "_Indicator_" + site_name + "_Chronicle"+ str(chronicle) + "_Approx" + str(approx) + "_K_" + str(permeability)

    if bve:
        dfglob.to_csv(mainRepo + output + "_BVE_CVHV_Extend.csv")
    else:
        dfglob.to_csv(mainRepo + output + "_CVHV.csv")

    print(mainRepo + output + "_BVE_CVHV_Extend.csv")


def createGlobalCSVFileSubCatch(indicator, folder, site, chronicle, approx, permeability, bve):
    """
    sitename : #Agon-Coutainville #Saint-Germain-Sur-Ay
    
    """
    site_name = utils.get_site_name_from_site_number(site)
    ref_name = utils.get_model_name(site, chronicle, None, None, ref=True, steady=False, permeability=permeability)

    mainRepo = folder + site_name + '/'
    
    if approx == 0 or approx == 2:
        approximations = [1.0, 2.0, 7.0, 15.0, 21.0, 30.0, 45.0, 50.0, 60.0, 75.0, 90.0, 100.0, 125.0, 150.0, 182.0, 200.0, 250.0, 300.0, 330.0, 365.0, 550.0, 640.0, 730.0, 1000.0, 1500.0, 2000.0, 2250.0, 3000.0, 3182.0, 3652.0]
        nb_lines = [0] * 30 # Fix: value not necessary! Or find the correct ones.
    else:
        approximations = [0, 0.0002, 0.05, 0.1, 0.2, 0.25, 0.4, 0.5, 0.8, 1.0, 2.0]
        nb_lines = [15341, 6597, 239, 122, 62, 50, 32, 26, 17, 14, 8]
    
    modelnames = [ref_name]
    for appr in range(1, len(approximations)):
         modelnames.append(utils.get_model_name(site, chronicle, approx, approximations[appr], ref=False, steady=False, permeability=permeability))

   
    dfglob = pd.DataFrame()

    for ind in range(len(modelnames)):
        simuRepo = modelnames[ind]
        if ind == 0:
            d = {'H Error': [0.0]}
            df = pd.DataFrame(data=d)
        else:
            if bve:
                filename = simuRepo + "_Ref_" + ref_name + "_errorsresult_" + indicator +"_BVE_SUB.csv"
            else:
                filename = simuRepo + "_Ref_" + ref_name + "_errorsresult_" + indicator +"_light.csv"
            try:
                df = pd.read_csv("/run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results/Igrida/" + filename, sep=";", header=False)
            except FileNotFoundError:
                print("File not Found: ", filename)
                continue
        print(df)
    
        taille = len(df.index)
        df_dur = pd.DataFrame(data=[approximations[ind]]*taille, index=df.index, columns=['Approximation'])
        #print(mainRepo + simuRepo + "/" + simuRepo + ".list")
        exec_time = getExecutionTimeFromListFile(mainRepo + simuRepo + "/" + simuRepo + ".list")
        if exec_time == -9:
            print("Time Execution Error for : ", simuRepo)
            continue
        df_time = pd.DataFrame(data=[exec_time]*taille, index=df.index, columns=['Execution Time'])
        df_lines = pd.DataFrame(data=[nb_lines[ind]]*taille, index=df.index, columns=['Number of Lines'])
        #df_geomorph = pd.read_csv("/DATA/These/OSUR/Extract_BV_june/" + str(site) + "_slope_elevation_Lc_Cw_A", sep=",")
        #print(df_geomorph)

        # print(df_dur)
        # print(df_time)
        # print(df_lines)

    #     with open("/DATA/These/OSUR/Extract_BV_june/" + str(site) + "_slope_elevation_Lc_Cw_A", newline='') as f:
    #         reader = csv.reader(f)
    #         geomorph = list(reader)



        crits = pd.read_csv(folder + "Geomorph_Features_All_Sites_Saturation_SubCatch.csv")
        #print(crits)

        # for site in [33, 34, 35, 37, 38, 39]

        tab = pd.DataFrame()


    #     vulne = pd.read_csv(mainRepo + "Feature_CV_HV_Site_"+ str(site)+"_BVE.csv", sep=";")
    #     #print(vulne["Coastal Vulnerability"][0])
    #     #print(geomorph)
    #     df_slope = pd.DataFrame(data=[float(geomorph[0][0])]*taille, index=df.index, columns=['Slope'])
    #     df_elev = pd.DataFrame(data=[float(geomorph[0][1])]*taille, index=df.index, columns=['Elevation'])
    #     df_Lc = pd.DataFrame(data=[float(geomorph[0][2])]*taille, index=df.index, columns=['LC'])
    #     df_Cw = pd.DataFrame(data=[float(geomorph[0][3])]*taille, index=df.index, columns=['CW'])
    #     df_A = pd.DataFrame(data=[float(geomorph[0][4])]*taille, index=df.index, columns=['Area'])
    #     df_CV =pd.DataFrame(data=[float(vulne["Coastal Vulnerability"][0])]*taille, index=df.index, columns=['CV'])
    #     df_HV =pd.DataFrame(data=[float(vulne["Hydrological Vulnerability"][0])]*taille, index=df.index, columns=['HV'])
    #     df = pd.concat([df, df_dur, df_time, df_lines, df_slope, df_elev, df_Lc, df_Cw, df_A, df_CV, df_HV], axis=1)
    #     dfglob = pd.concat([dfglob,df])

    # output = "Exps_" + indicator + "_Indicator_" + site_name + "_Chronicle"+ str(chronicle) + "_Approx" + str(approx) + "_K_" + str(permeability)

    # if bve:
    #     dfglob.to_csv(mainRepo + output + "_BVE_CVHV_Extend.csv")
    # else:
    #     dfglob.to_csv(mainRepo + output + "_CVHV.csv")

    # print(mainRepo + output + "_BVE_CVHV_Extend.csv")







if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    #parser.add_argument("-ind", "--indicator", type=str, required=True)
    parser.add_argument("-site", "--site", type=int, help= "2: Agon-Coutainville or 3:Saint-Germain-Sur-Ay", required=True)
    parser.add_argument("-approx", "--approximation", type=int, required=True)
    parser.add_argument("-chr", "--chronicle", type=int)
    parser.add_argument("-f", "--folder", type=str, required=True)
    parser.add_argument("-perm", "--perm", type=float, required=True)
    parser.add_argument("-bve", "--bve", action='store_true')
    parser.add_argument("-test", "--test", action='store_true')
    args = parser.parse_args()
    
    site = args.site
    chronicle = args.chronicle
    #indicator = args.indicator
    folder= args.folder
    approx = args.approximation
    permeability = args.perm
    bve = args.bve
    test = args.test

    indicator = "H"
    
    if test:
        createGlobalCSVFileSubCatch(indicator, folder, site, chronicle, approx, permeability, bve)
    else:
        createGlobalCSVFile(indicator, folder, site, chronicle, approx, permeability, bve)