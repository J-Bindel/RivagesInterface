import os
import pandas as pd
import argparse
from custom_utils import helpers as utils


def compute_execTime_for_all_sites(folder, chronicle, approx, indicator):
    sites = [1,2,4,5,6,7,8,10,11,12,13,15,17,18,19,21,22,23,24,26,28,29,30]
    
    df = pd.DataFrame(columns=["Site", "ExecTimeSum"])
    for site_number in sites:
        sum_execTime = 0
        model_name = utils.get_model_name(site_number, chronicle, approx, rate=1.0, ref=True)
        site_name = utils.get_site_name_from_site_number(site_number)
        name = "Exps_" + indicator + "_Indicator_" + site_name + "_Chronicle"+ str(chronicle) + "_Approx" + str(approx)

        file = folder + "/" + site_name + "/" + name + ".csv"
        dfp = pd.read_csv(file, sep=",")

        sum_execTime += dfp["Execution Time"].sum()

        row = {"Site" : str(site_name), "ExecTimeSum" : sum_execTime}
        df = df.append(row, ignore_index=True)
    df.to_csv(folder + "/" + "AllSites_ExecTimeSum_Chr" + str(chronicle) + "_Approx" + str(approx) + ".csv",sep="\t", index=False)




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-ind", "--indicator", type=str, required=True)
    parser.add_argument("-site", "--site", type=int, help= "2: Agon-Coutainville or 3:Saint-Germain-Sur-Ay", required=False)
    parser.add_argument("-chr", "--chronicle", type=int)
    parser.add_argument("-approx", "--approximation", type=int)
    parser.add_argument("-f", "--folder", type=str, required=True)

    args = parser.parse_args()
    
    chronicle = args.chronicle
    approx=args.approximation
    indicator = args.indicator
    folder = args.folder

    compute_execTime_for_all_sites(folder, chronicle, approx, indicator)