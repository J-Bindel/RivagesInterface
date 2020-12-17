# coding:utf-8
import numpy as np
import matplotlib.pyplot as plt
import pyproj
import matplotlib.colors as colors
import geopandas as gpd
from pysheds.grid import Grid
import mplleaflet
import seaborn as sns

import warnings
warnings.filterwarnings('ignore')
sns.set_palette('husl')

# Instatiate a grid from a raster
grid = Grid.from_raster('H:/Users/gauvain/DEM/data/MNT_TOPO_BATH_75m.tif', data_name='dem')
#grid.dem[grid.dem<0]=np.nan
depressions = grid.detect_depressions('dem')
grid.fill_depressions(data='dem', out_name='flooded_dem')
depressions = grid.detect_depressions('dem')
#depressions.any()
flats = grid.detect_flats('flooded_dem')
grid.resolve_flats(data='flooded_dem', out_name='inflated_dem')
plt.figure()
plt.imshow(depressions)


# Plot the raw DEM data
fig, ax = plt.subplots(figsize=(8,6))
plt.imshow(grid.dem, extent=grid.extent, cmap='cubehelix', zorder=1)
plt.colorbar(label='Elevation (m)')
plt.title('Digital elevation map')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

#N    NE    E    SE    S    SW    W    NW
dirmap = (64,  128,  1,   2,    4,   8,    16,  32)
grid.flowdir(data='inflated_dem', out_name='dir', dirmap=dirmap, pits=-2)

# Plot the flow direction grid
fig = plt.figure(figsize=(8,6))
plt.imshow(grid.dir, extent=grid.extent, cmap='viridis', zorder=1)
boundaries = ([0] + sorted(list(dirmap)))
plt.colorbar(boundaries= boundaries,
             values=sorted(dirmap))
plt.title('Flow direction grid')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Specify pour point
x, y = 363558, 6894400
# Compute flow accumulation at each cell
grid.accumulation(data='dir', dirmap=dirmap, out_name='acc', pad=True)
# Get a view and add 1 (to help with log-scaled colors)
acc = grid.view('acc', nodata=np.nan) + 1
acc[grid.dem<0]=np.nan
# Plot the result
fig, ax = plt.subplots(figsize=(8,6))
im = ax.imshow(acc, extent=grid.extent, zorder=1,
               cmap='cubehelix',
               norm=colors.LogNorm(1, grid.acc.max()))
plt.colorbar(im, ax=ax, label='Upstream Cells')
ax.scatter(x, y, s=5000, c='r')
plt.title('Flow Accumulation')
plt.xlabel('Longitude')
plt.ylabel('Latitude')


# Delineate the catchment
grid.catchment(data='dir', x=x, y=y, dirmap=dirmap, out_name='catch',
               recursionlimit=15000, xytype='label', nodata_out=0)
# Clip the bounding box to the catchment
grid.clip_to('catch',precision=7)
# Get a view of the catchment corresponding to the current bounding box
catch = grid.view('catch', nodata=np.nan)
# Plot the catchment
fig, ax = plt.subplots(figsize=(8,6))
im = ax.imshow(catch, extent=grid.extent, zorder=1, cmap='viridis')
plt.colorbar(im, ax=ax, boundaries=boundaries, values=sorted(dirmap),
             label='Flow Direction')
plt.title('Delineated Catchment')
plt.xlabel('Longitude')
plt.ylabel('Latitude')



plt.show()





# Delineate the catchment
grid.catchment(data=grid.dir, x=x, y=y, dirmap=dirmap, out_name='catch',
               recursionlimit=100, xytype='label', nodata_out=0, routing='d8')
# Clip the bounding box to the catchment
grid.clip_to('catch')
# Get a view of the catchment
demView = grid.view('dem',nodata=np.nan)
plotFigure(demView,'Elevation')
#export selected raster
grid.accumulation(data='dem', dirmap=dirmap, pad_inplace=False, out_name='acc')

accView = grid.view('acc', nodata=np.nan)
plotFigure(accView,"Cell Number",'PuRd')
streams = grid.extract_river_network('catch', 'acc', threshold=200, dirmap=dirmap)
streams["features"][:2]
def saveDict(dic,file):
    f = open(file,'w')
    f.write(str(dic))
    f.close()
#save geojson as separate file
saveDict(streams,'H:/Users/gauvain/DEM/data/streams.geojson')

streamNet = gpd.read_file('H:/Users/gauvain/DEM/data//streams.geojson')
streamNet.crs = {'init' :'epsg:2154'}
# The polygonize argument defaults to the grid mask when no arguments are supplied
shapes = grid.polygonize()

# Plot catchment boundaries
fig, ax = plt.subplots(figsize=(6.5, 6.5))

for shape in shapes:
    coords = np.asarray(shape[0]['coordinates'][0])
    ax.plot(coords[:,0], coords[:,1], color='cyan')

ax.set_xlim(grid.bbox[0], grid.bbox[2])
ax.set_ylim(grid.bbox[1], grid.bbox[3])
ax.set_title('Catchment boundary (vector)')
gpd.plotting.plot_dataframe(streamNet, None, cmap='Blues', ax=ax)
#ax = streamNet.plot()
mplleaflet.display(fig=ax.figure, crs=streamNet.crs, tiles='esri_aerial')
plt.show()