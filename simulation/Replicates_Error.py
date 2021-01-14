import re
import os
import numpy as np
import pandas as pd
import argparse

from custom_utils import helpers as utils



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
        #print(m.group(2), m.group(3), m.group(4), exec_time)
    else:
        exec_time = int(m.group(1))*24*60*60 + int(m.group(2))*60*60 + int(m.group(3))*60 + float(m.group(4))
    return int(exec_time)


def create_CSV_File_With_Time_Of_Replicates(site_number, replicate_number, chronicle, approx, rate, folder, ref):

    site_name = utils.get_site_name_from_site_number(site_number)
    model_name = utils.get_model_name(site_number, chronicle, approx, rate, ref)
    

    df = pd.DataFrame(columns=["Replicate", "ExecTime"])

    for rep in range(1, replicate_number+1):
        # if rep in (4, 7, 8, 9, 11, 12, 18, 24, 26):
        #      pass
        # else:
        exec_time = getExecutionTimeFromListFile(folder + "/" + site_name + "/" + model_name + "_" + str(rep) + "/" + model_name + "_" + str(rep) + ".list")
        row = {"Replicate" : str(rep), "ExecTime" : exec_time}
        df = df.append(row, ignore_index=True)
            #df["Replicate"] = str(rep)
            #df["ExecTime"] = exec_time
            
    print(df.describe())
    print(df["ExecTime"].mean())
    print(df["ExecTime"].median())
    print(df["ExecTime"].std())
    df.to_csv(folder + "/" + site_name + "/" + "Exec_Time_Of_"+ str(replicate_number) + "_ForChr" + str(chronicle) + "_Approx" + str(approx) + "_Rate" + str(rate) + ".csv", sep=";", index=False)
    print(folder + "/" + site_name + "/" + "Exec_Time_Of_"+ str(replicate_number) + "_ForChr" + str(chronicle) + "_Approx" + str(approx) + "_Rate" + str(rate) + ".csv")
    with open(folder + "/" + site_name + "/" + "Stats_for_Rep" + str(replicate_number) + "_ForChr" + str(chronicle) + "_Approx" + str(approx) + "_Rate" + str(rate) + '.txt', 'w') as f: 
        f.write('Mean: ' + str(df["ExecTime"].mean()) +'\n')
        f.write('Median: ' + str(df["ExecTime"].median()) +'\n')
        f.write('Standard Dev: ' + str(df["ExecTime"].std()) +'\n')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-site", "--site", type=int, help= "2: Agon-Coutainville or 3:Saint-Germain-Sur-Ay", required=True)
    parser.add_argument("-approx", "--approximation", type=int, required=True)
    parser.add_argument("-chr", "--chronicle", type=int)
    parser.add_argument("-rate", "--rate", type=float, required=True)
    parser.add_argument("-f", "--folder", type=str, required=True)
    parser.add_argument("-ref", "--ref", action='store_true')
    parser.add_argument("-rep", "--replicate", type=int)

    args = parser.parse_args()
    
    site_number = args.site
    chronicle = args.chronicle
    folder= args.folder
    approx = args.approximation
    rate = args.rate
    ref = args.ref
    replicate_number = args.replicate

    create_CSV_File_With_Time_Of_Replicates(site_number, replicate_number, chronicle, approx, rate, folder, ref)