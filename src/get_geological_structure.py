# coding:utf-8

import flopy
import os
import sys

data_src = os.getcwd() + '//data'            #DATA FOLDER
sys.path.append(os.getcwd() + '//data')       #SOURCES

import numpy as np
import pandas as pd
from osgeo import gdal, gdalconst
from osgeo import osr, ogr
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import subprocess
from scipy import interpolate
import whitebox
wbt = whitebox.WhiteboxTools()
wbt.set_verbose_mode(False)
import geopandas as gpd
from IPython.core.debugger import set_trace as st

class structure:
    def __init__(self,code):
        #Files path
        self.r_dem = data_src + "/MNT_TOPO_BATH_75m.tif"
        self.r_k = data_src + "/GLHYMPS.tif"
        self.r_gum = data_src + "/GUM.tif"
        self.r_bedrock_depth = data_src + "/bedrock_depth.tif"
        self.r_sea_earth = data_src + "/sea_earth2.tif"
        self.r_river = data_src + "/river_75m.tif"
        self.r_geol = data_src + "/geology/GEO1M.shp" #"/geology/GEO50K.shp"
        self.r_hydro = data_src + "/Hydro_net/TronconHydrographique_FXX.shp"
        self.r_zone_hydro = data_src + "/Hydro_net/ZONE_HYDROGRAPHIQUE_COTIER.shp"
        self.r_ram = data_src + "/Hydro_net/RAM_2020.shp"
        self.tmp = data_src + "/tmp/"
        self.r_watershed_shp = self.tmp + "watershed.shp"
        self.r_watershed = data_src + '/tmp/watershed.tif'
        self.r_geo = data_src + '/tmp/geology.tif'
        self.r_terre_mer = data_src + '/tmp/terre_mer.tif'
        self.r_hydro_net= data_src + '/tmp/hydro_net.tif'
        
        #Data
        self.code = code
        self.get_coord()
        self.get_mean_sea_level()
        self.get_model_size()
        self.dem = self.get_clip_dem()
        self.save_clip_dem()
        self.get_geology()
        self.get_watershed()
        self.get_hydrographic_network()
        
        self.river = self.get_clip_river()
        self.sea_earth = self.get_clip_sea_earth()
        self.K = self.get_clip_K()
        self.gum = self.get_clip_gum()
        self.bedrock_depth = self.get_clip_bedrock_depth()
        
    def get_coord(self):
        gdf = gpd.read_file(self.r_zone_hydro)
        gdf = gdf.to_crs(epsg=2154)
        self.BV = gdf[gdf.CODE_ZONE==self.code]
        coord = self.BV.bounds
        self.coord = np.ones(4)
        x_len = coord.maxx - coord.minx
        y_len = coord.maxy - coord.miny
        buffer = 0.1
        self.coord[0]= coord.minx - x_len*buffer
        self.coord[1]= coord.maxx + x_len*buffer
        self.coord[2]= coord.miny - y_len*buffer
        self.coord[3]= coord.maxy + y_len*buffer
    
    def get_mean_sea_level(self):
        gdf = gpd.read_file(self.r_ram)
        ports = gdf.to_crs(epsg=2154)
        #ports = gdf[gdf.NM>0]
        centroid = self.BV.centroid
        dist = np.sqrt((centroid.geometry.x.values-ports.geometry.x.values)**2+(centroid.geometry.y.values-ports.geometry.y.values)**2)
        index = (np.abs(dist)).argmin()
        ports.SITE[index]
        self.mean_sea_level = ports.NM[index]/100+ports.ZH_Ref[index]
    
    def get_watershed(self):
        self.BV.to_file(self.r_watershed_shp)
        wbt.vector_polygons_to_raster(self.r_watershed_shp, self.r_watershed,field="CODE_ZONE", nodata=None, base=self.tmp + 'MNT_tmp.tif')
        dem_geo = gdal.Open(self.r_watershed)
        dem_data = dem_geo.GetRasterBand(1).ReadAsArray()
        self.watershed = dem_data
    
    def get_geology(self):
        wbt.vector_polygons_to_raster(self.r_geol, self.r_geo, field="CODE_LEG", nodata=None, base=self.tmp + 'MNT_tmp.tif')
        wbt.vector_polygons_to_raster(self.r_geol, self.r_terre_mer, field="T_M_num", nodata=None, base=self.tmp + 'MNT_tmp.tif')
        dem_geo = gdal.Open(self.r_geo)
        dem_data = dem_geo.GetRasterBand(1).ReadAsArray()
        dem_T_M = gdal.Open(self.r_terre_mer)
        dem_data_T_M = dem_T_M.GetRasterBand(1).ReadAsArray()
        dem_data[dem_data<1000] = 1
        dem_data[dem_data>=1000] = 2
        dem_data[dem_data_T_M==0] = 1
        self.geology = dem_data.astype(int)
    
    def get_hydrographic_network(self):
        wbt.vector_lines_to_raster(self.r_hydro, self.r_hydro_net, field="Percistanc", nodata=None, base=self.tmp + 'MNT_tmp.tif')
        dem = gdal.Open(self.r_hydro_net)
        dem_data = dem.GetRasterBand(1).ReadAsArray()
        self.hydro_network = dem_data.astype(int)
        
    def get_clip_dem(self):
        dem = gdal.Open(self.r_dem)
        dem_data = dem.GetRasterBand(1).ReadAsArray()
        return dem_data[self.ulY:self.lrY, self.ulX:self.lrX]
    
    def save_clip_dem(self):
        drv = gdal.GetDriverByName("GTiff")
        ds = drv.Create(self.tmp + 'MNT_tmp.tif',self.dem.shape[1], self.dem.shape[0], 1, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(2154)
        ds.SetProjection(srs.ExportToWkt())
        gt = [self.dem_x[0],self.geot[1], 0, self.dem_y[1], 0, self.geot[5]]
        ds.SetGeoTransform(gt)
        ds.GetRasterBand(1).WriteArray(self.dem)
        
    def get_model_size(self):
        xmin = self.coord[0]
        xmax = self.coord[1]
        ymin = self.coord[2]
        ymax = self.coord[3]
        dem = gdal.Open(self.r_dem)
        self.geot = dem.GetGeoTransform()
        dem_Xpos = np.ones((dem.RasterXSize))
        dem_Ypos = np.ones((dem.RasterYSize))
        for i in range(0, dem.RasterYSize):
            yp = self.geot[3] + (self.geot[5] * i)
            dem_Ypos[i] = yp
        for j in range(0, dem.RasterXSize):
            xp = self.geot[0] + (self.geot[1] * j)
            dem_Xpos[j] = xp
        self.ulX = (np.abs(dem_Xpos - xmin)).argmin()
        self.lrX = (np.abs(dem_Xpos - xmax)).argmin()
        self.ulY = (np.abs(dem_Ypos - ymax)).argmin()
        self.lrY = (np.abs(dem_Ypos - ymin)).argmin()
        self.dem_x = dem_Xpos[self.ulX:self.lrX]
        self.dem_y = dem_Ypos[self.ulY:self.lrY]

    def get_clip_river(self):
        dem = gdal.Open(self.r_river)
        dem_data = dem.GetRasterBand(1).ReadAsArray()
        clip_dem = dem_data[self.ulY:self.lrY, self.ulX:self.lrX]
        return clip_dem
        
    def get_clip_sea_earth(self):
        sea_earth = gdal.Open(self.r_sea_earth)
        sea_earth_data = sea_earth.GetRasterBand(1).ReadAsArray()
        clip_sea_earth = sea_earth_data[self.ulY:self.lrY, self.ulX:self.lrX]
        return clip_sea_earth

    def get_clip_K(self):
        k = gdal.Open(self.r_k)
        k_data = k.GetRasterBand(1).ReadAsArray()
        clip_K = k_data[self.ulY:self.lrY, self.ulX:self.lrX]
        clip_K[clip_K == 0] = -999998
        clip_K[clip_K == -999998] = np.max(clip_K)
        clip_K = 10 ** (clip_K / 100) * 1e+7
        return clip_K

    def get_clip_gum(self):
        gum = gdal.Open(self.r_gum)
        gum_data = gum.GetRasterBand(1).ReadAsArray()
        clip_gum = gum_data[self.ulY:self.lrY, self.ulX:self.lrX]
        clip_gum[self.dem == -99999.0] = 3
        clip_gum[clip_gum == 0] = 2
        return clip_gum

    def get_clip_bedrock_depth(self):
        bd = gdal.Open(self.r_bedrock_depth)
        bd_data = bd.GetRasterBand(1).ReadAsArray()
        clip_bd = bd_data[self.ulY:self.lrY,self. ulX:self.lrX]/100
        return clip_bd

def save_clip_lidar(site_number):
    forestcover = "data/Lidar1m.tif"
    sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
    coord = sites._get_values[site_number, 1:5]
    save_clip_dem(site_number)
    site_name = sites.axes[0][site_number]
    clip = site_name+'/'+site_name+'_MNT.tif'
    # output files
    cutline = site_name+'/cutline.shp'
    result = site_name+'/'+site_name+'_lidar1m.tif'
    # create the cutline polygon
    cutline_cmd = ["gdaltindex", cutline, clip]
    subprocess.check_call(cutline_cmd)
    # crop forestcover to cutline
    # Note: leave out the -crop_to_cutline option to clip by a regular bounding box
    warp_cmd = ["gdalwarp", "-of", "GTiff", "-cutline", cutline,"-crop_to_cutline", forestcover, result]
    subprocess.check_call(warp_cmd)

def save_clip_mnt5m(site_number):
    forestcover = "data/MNT5m.tif"
    sites = pd.read_table("study_sites.txt", sep='\s+', header=0, index_col=0)
    coord = sites._get_values[site_number, 1:5]
    save_clip_dem(site_number)
    site_name = sites.axes[0][site_number]
    clip = site_name+'/'+site_name+'_MNT.tif'
    # output files
    cutline = site_name+'/cutline.shp'
    result = site_name+'/'+site_name+'_mnt5m.tif'
    # create the cutline polygon
    cutline_cmd = ["gdaltindex", cutline, clip]
    subprocess.check_call(cutline_cmd)
    # crop forestcover to cutline
    # Note: leave out the -crop_to_cutline option to clip by a regular bounding box
    warp_cmd = ["gdalwarp", "-of", "GTiff", "-cutline", cutline,"-crop_to_cutline", forestcover, result]
    subprocess.check_call(warp_cmd)



#ibndDs = gdal.GetDriverByName('GTiff').Create('ibound.tif',demDs.RasterXSize, demDs.RasterYSize, 1, gdal.GDT_Int32)
#ibndDs.SetProjection(demDs.GetProjection())
#ibndDs.SetGeoTransform(geot)






