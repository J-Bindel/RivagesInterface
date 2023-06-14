
folder = "/run/media/jnsll/b0417344-c572-4bf5-ac10-c2021d205749/exps_modflops/results"
site_number = 11
indicator = "H"
#for site_number in range(1,31):
site_name = get_site_name_from_site_number(site_number)
df_all_per_site = pd.DataFrame()

for site_number in range(31):
    for approx in range(2):
        for chronicle in range(2):
            df = get_csv_file_with_indicator_for_a_context(site_number, chronicle, approx, folder)
            if not df.empty:
                taille = len(df.index)
                df = df.drop(df.columns[[0]], axis=1)
                df.rename(columns={'Approximation':'Rate'}, inplace=True)
                df_site = pd.DataFrame(data=[site_number]*taille, index=df.index, columns=['Site_number'])
                df_approx = pd.DataFrame(data=[approx]*taille, index=df.index, columns=['Approx'])
                df_chr = pd.DataFrame(data=[chronicle]*taille, index=df.index, columns=['Chronicle'])
                #steady features 
                df_steady_uni = get_csv_file_with_steady_features_for_a_context(site_number, chronicle, folder)
                df_steady = pd.concat([df_steady_uni]*taille, ignore_index=True)
                df_geomorph = 
                dff = pd.concat([df_site, df_approx, df_chr, df, df_steady], axis=1)        

                df_all_per_site = pd.concat([df_all_per_site, dff])

    output_file_name = "Exps_" + indicator + "_Indicator_" + site_name + "_BVE.csv"
    print(output_file_name)
    df_all_per_site.to_csv(folder + "/" + site_name + "/" + output_file_name, index=False)