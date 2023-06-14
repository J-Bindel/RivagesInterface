# coding: utf-8

import os, re
import numpy as np
from osgeo import gdal
import flopy
from flopy.export import vtk as fv
import vtk
import flopy.utils.binaryfile as bf
from simulation.get_geological_structure import get_geological_structure as ggs
from src.custom_utils.workingFunctions import Functions # functions from the workingFunctions.py file

print('Import Georeferences')


def GetExtent(gt, geotx, geoty, cols, rows):
    ext = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = geotx[0] + (px * gt[1]) + (py * gt[2])
            y = geoty[0] + (px * gt[4]) + (py * gt[5])
            ext.append([x, y])
            print(x, y)
        yarr.reverse()
    return ext
modelfolder = 'H:/Users/gauvain/DEM/Guidel/'
modelname = 'Guidel1'

mf1 = flopy.modflow.Modflow()
dis = flopy.modflow.ModflowDis.load(modelfolder+modelname+'.dis',mf1)

cols = dis.ncol
rows = dis.nrow


# change directory to the script path
os.chdir(modelfolder)  # use your own path

# open the DIS, BAS files
disLines = open(modelfolder + modelname + '.dis').readlines()  # discretization data
basLines = open(modelfolder + modelname + '.bas').readlines()  # active / inactive data

# create a empty dictionay to store the model features
modDis = {}
modBas = {}

# # Working with the DIS (Discretization Data) data

# ### General model features as modDis dict

# In[3]:

# get the extreme coordinates form the dis header

modDis["vertexXmin"] = 0
modDis["vertexYmin"] = 0
modDis["vertexXmax"] = 3670
modDis["vertexYmax"] = 2930

# get the number of layers, rows, columns, cell and vertex numbers
linelaycolrow = disLines[1].split()
modDis["cellLays"] = int(linelaycolrow[0])
modDis["cellRows"] = int(linelaycolrow[1])
modDis["cellCols"] = int(linelaycolrow[2])
modDis["vertexLays"] = modDis["cellLays"] + 1
modDis["vertexRows"] = modDis["cellRows"] + 1
modDis["vertexCols"] = modDis["cellCols"] + 1
modDis["vertexperlay"] = modDis["vertexRows"] * modDis["vertexCols"]
modDis["cellsperlay"] = modDis["cellRows"] * modDis["cellCols"]

# ### Get the DIS Breakers

# In[4]:
print('Import DIS')

# get the grid breakers
modDis['disBreakers'] = {}
breakerValues = ["INTERNAL", "CONSTANT"]

vertexLay = 0
for item in breakerValues:
    for line in disLines:
        if item in line:
            if 'delr' in line:  # DELR is cell width along rows
                modDis['disBreakers']['DELR'] = disLines.index(line)
            elif 'delc' in line:  # DELC is cell width along columns
                modDis['disBreakers']['DELC'] = disLines.index(line)
            else:
                modDis['disBreakers']['vertexLay' + str(vertexLay)] = disLines.index(line)
                vertexLay += 1

# ### Get the DEL Info

# In[5]:

modDis['DELR'] = Functions.getListFromDEL(modDis['disBreakers']['DELR'], disLines, modDis['cellCols'])
modDis['DELC'] = Functions.getListFromDEL(modDis['disBreakers']['DELC'], disLines, modDis['cellRows'])

# ### Get the Cell Centroid Z

# In[6]:

modDis['cellCentroidZList'] = {}

for lay in range(modDis['vertexLays']):

    # add auxiliar variables to identify breakers
    lineaBreaker = modDis['disBreakers']['vertexLay' + str(lay)]
    # two cases in breaker line
    if 'INTERNAL' in disLines[lineaBreaker]:
        lista = Functions.getListFromBreaker(lineaBreaker, modDis, disLines)
        modDis['cellCentroidZList']['lay' + str(lay)] = lista
    elif 'CONSTANT' in disLines[lineaBreaker]:
        constElevation = float(disLines[lineaBreaker].split()[1])
        modDis['cellCentroidZList']['lay' + str(lay)] = [constElevation for x in range(modDis["cellsperlay"])]
    else:
        pass

# ### List of arrays of cells and vertex coord

# In[7]:

modDis['vertexEasting'] = np.array(
    [modDis['vertexXmin'] + np.sum(modDis['DELR'][:col]) for col in range(modDis['vertexCols'])])
modDis['vertexNorthing'] = np.array(
    [modDis['vertexYmax'] - np.sum(modDis['DELC'][:row]) for row in range(modDis['vertexRows'])])

modDis['cellEasting'] = np.array(
    [modDis['vertexXmin'] + np.sum(modDis['DELR'][:col]) + modDis['DELR'][col] / 2 for col in
     range(modDis['cellCols'])])
modDis['cellNorthing'] = np.array(
    [modDis['vertexYmax'] - np.sum(modDis['DELC'][:row]) - modDis['DELC'][row] / 2 for row in
     range(modDis['cellRows'])])

# ### Interpolation from Z cell centroid to z vertex

# # Get the BAS Info

# ### Get the grid breakers

# In[8]:
print('Import DATA')

# empty dict to store BAS breakers
modBas['basBreakers'] = {}

breakerValues = ["INTERNAL", "CONSTANT"]

# store the breakers in the dict
lay = 0
for item in breakerValues:
    for line in basLines:
        if item in line:
            if 'ibound' in line:
                modBas['basBreakers']['lay' + str(lay)] = basLines.index(line)
                lay += 1
            else:
                pass

# ### Store ibound per lay

# In[9]:

# empty dict to store cell ibound per layer
modBas['cellIboundList'] = {}

for lay in range(modDis['cellLays']):

    # add auxiliar variables to identify breakers
    lineaBreaker = modBas['basBreakers']['lay' + str(lay)]

    # two cases in breaker line
    if 'INTERNAL' in basLines[lineaBreaker]:
        lista = Functions.getListFromBreaker(lineaBreaker, modDis, basLines)
        modBas['cellIboundList']['lay' + str(lay)] = lista
    elif 'CONSTANT' in basLines[lineaBreaker]:
        constElevation = float(disLines[lineaBreaker].split()[1])  # todavia no he probado esto
        modBas['cellIboundList']['lay' + str(lay)] = [constElevation for x in range(modDis["cellsperlay"])]
    else:
        pass

# ### Store Cell Centroids as a Numpy array

# In[10]:

# empty list to store cell centroid
cellCentroidList = []

# numpy array of cell centroid
for row in range(modDis['cellRows']):
    for col in range(modDis['cellCols']):
        cellCentroidList.append([modDis['cellEasting'][col], modDis['cellNorthing'][row]])

# store cell centroids as numpy array
modDis['cellCentroids'] = np.asarray(cellCentroidList)
modDis['vertexXgrid'] = np.repeat(modDis['vertexEasting'].reshape(modDis['vertexCols'], 1), modDis['vertexRows'],
                                  axis=1).T
modDis['vertexYgrid'] = np.repeat(modDis['vertexNorthing'], modDis['vertexCols']).reshape(modDis['vertexRows'],
                                                                                          modDis['vertexCols'])
modDis['vertexZGrid'] = Functions.interpolateCelltoVertex(modDis, 'cellCentroidZList')

# # Lists for the VTK file

# ### Definition of xyz points for all vertex

# In[22]:

# empty list to store all vertex XYZ
vertexXYZPoints = []

# definition of xyz points for all vertex
for lay in range(modDis['vertexLays']):
    for row in range(modDis['vertexRows']):
        for col in range(modDis['vertexCols']):
            xyz = [
                modDis['vertexEasting'][col],
                modDis['vertexNorthing'][row],
                modDis['vertexZGrid']['lay' + str(lay)][row, col]
            ]
            vertexXYZPoints.append(xyz)

# In[25]:

# empty list to store all ibound
listIBound = []
listHk = []
listFlow = []
# definition of IBOUND
for lay in range(modDis['cellLays']):
    for item in modBas['cellIboundList']['lay' + str(lay)]:
        listIBound.append(item)


# ### Definition of Cell Ibound List

# In[28]:

# # Hexahedrons and Quads sequences for the VTK File

# ### List of Layer Quad Sequences (Works only for a single layer)

# In[29]:

# empty list to store cell coordinates
listLayerQuadSequence = []

# definition of hexahedrons cell coordinates
for row in range(modDis['cellRows']):
    for col in range(modDis['cellCols']):
        pt0 = modDis['vertexCols'] * (row + 1) + col
        pt1 = modDis['vertexCols'] * (row + 1) + col + 1
        pt2 = modDis['vertexCols'] * (row) + col + 1
        pt3 = modDis['vertexCols'] * (row) + col
        anyList = [pt0, pt1, pt2, pt3]
        listLayerQuadSequence.append(anyList)

# ### List of Hexa Sequences

# In[30]:

# empty list to store cell coordinates
listHexaSequence = []

# definition of hexahedrons cell coordinates
for lay in range(modDis['cellLays']):
    for row in range(modDis['cellRows']):
        for col in range(modDis['cellCols']):
            pt0 = modDis['vertexperlay'] * (lay + 1) + modDis['vertexCols'] * (row + 1) + col
            pt1 = modDis['vertexperlay'] * (lay + 1) + modDis['vertexCols'] * (row + 1) + col + 1
            pt2 = modDis['vertexperlay'] * (lay + 1) + modDis['vertexCols'] * (row) + col + 1
            pt3 = modDis['vertexperlay'] * (lay + 1) + modDis['vertexCols'] * (row) + col
            pt4 = modDis['vertexperlay'] * (lay) + modDis['vertexCols'] * (row + 1) + col
            pt5 = modDis['vertexperlay'] * (lay) + modDis['vertexCols'] * (row + 1) + col + 1
            pt6 = modDis['vertexperlay'] * (lay) + modDis['vertexCols'] * (row) + col + 1
            pt7 = modDis['vertexperlay'] * (lay) + modDis['vertexCols'] * (row) + col
            anyList = [pt0, pt1, pt2, pt3, pt4, pt5, pt6, pt7]
            listHexaSequence.append(anyList)

# ### Active Cells and Hexa Sequences

# In[32]:

listActiveHexaSequenceDef = []
listIBoundDef = []
listHkDef = []
listFlowDef = []

# filter hexahedrons and heads for active cells
for i in range(len(listIBound)):
    if listIBound[i] > -10:
        listActiveHexaSequenceDef.append(listHexaSequence[i])
        listIBoundDef.append(listIBound[i])


# In[34]:

# # VTK creation

# ### Summary of lists for the vtk creation

# In[35]:

### Point sets
#   vertexXYZPoints                    for XYZ in all cell vertex
#   vertexWaterTableXYZPoints          for XYZ in all water table quad vertex
#   listDrainCellQuadXYZPoints         for XYZ in all drain cells quad vertex

### Quad and Hexa secuences
#   listHexaSequenceDef                for Head Hexa Sequence in all active cells
#   listActiveHexaSequenceDef          for Active Hexa Sequence in all active cells
#   listWaterTableQuadSequenceDef      for Water Table Quad Sequence in all active cells
#   listDrainsCellsSecuenceDef         for Drain Cell Quad Sequence in drain cells

### Cell data
#   listCellHeadDef                    for filtered active cells
#   listIBoundDef
#   listWaterTableCellDef              for filtered water table cells
#   listDrainsCellsIODef               for filtered drains cells

### Point data
#   listVertexHead                     for heads in all cells

# ### Heads on Vertex and Cells VTK

# In[36]:

# ### Active Cell VTK

# In[37]:

print('Create files')
textoVtk = open(modelfolder + 'output_files/VTU_Grid.vtu', 'w')

# add header
textoVtk.write('<VTKFile type="UnstructuredGrid" version="1.0" byte_order="LittleEndian" header_type="UInt64">\n')
textoVtk.write('  <UnstructuredGrid>\n')
textoVtk.write('    <Piece NumberOfPoints="' + str(len(vertexXYZPoints)) + '" NumberOfCells="' + str(
    len(listActiveHexaSequenceDef)) + '">\n')

# cell data
textoVtk.write('      <CellData Scalars="Model">\n')
textoVtk.write('        <DataArray type="Int32" Name="Active" format="ascii">\n')
for item in range(len(listIBoundDef)):  # cell list
    textvalue = str(int(listIBoundDef[item]))
    if item == 0:
        textoVtk.write('          ' + textvalue + ' ')
    elif item % 20 == 0:
        textoVtk.write(textvalue + '\n          ')
    else:
        textoVtk.write(textvalue + ' ')
textoVtk.write('\n')
textoVtk.write('        </DataArray>\n')


textoVtk.write('      </CellData>\n')

# points definition
textoVtk.write('      <Points>\n')
textoVtk.write('        <DataArray type="Float64" Name="Points" NumberOfComponents="3" format="ascii">\n')
for item in range(len(vertexXYZPoints)):
    tuplevalue = tuple(vertexXYZPoints[item])
    if item == 0:
        textoVtk.write("          %.2f %.2f %.2f " % tuplevalue)
    elif item % 4 == 0:
        textoVtk.write('%.2f %.2f %.2f \n          ' % tuplevalue)
    elif item == len(vertexXYZPoints) - 1:
        textoVtk.write("%.2f %.2f %.2f \n" % tuplevalue)
    else:
        textoVtk.write("%.2f %.2f %.2f " % tuplevalue)
textoVtk.write('        </DataArray>\n')
textoVtk.write('      </Points>\n')

# cell connectivity
textoVtk.write('      <Cells>\n')
textoVtk.write('        <DataArray type="Int64" Name="connectivity" format="ascii">\n')
for item in range(len(listActiveHexaSequenceDef)):
    textoVtk.write('          ')
    textoVtk.write('%s %s %s %s %s %s %s %s \n' % tuple(listActiveHexaSequenceDef[item]))
textoVtk.write('        </DataArray>\n')
# cell offsets
textoVtk.write('        <DataArray type="Int64" Name="offsets" format="ascii">\n')
for item in range(len(listActiveHexaSequenceDef)):
    offset = str((item + 1) * 8)
    if item == 0:
        textoVtk.write('          ' + offset + ' ')
    elif item % 20 == 0:
        textoVtk.write(offset + ' \n          ')
    elif item == len(listActiveHexaSequenceDef) - 1:
        textoVtk.write(offset + ' \n')
    else:
        textoVtk.write(offset + ' ')
textoVtk.write('        </DataArray>\n')
# cell types
textoVtk.write('        <DataArray type="UInt8" Name="types" format="ascii">\n')
for item in range(len(listActiveHexaSequenceDef)):
    if item == 0:
        textoVtk.write('          ' + '12 ')
    elif item % 20 == 0:
        textoVtk.write('12 \n          ')
    elif item == len(listActiveHexaSequenceDef) - 1:
        textoVtk.write('12 \n')
    else:
        textoVtk.write('12 ')
textoVtk.write('        </DataArray>\n')
textoVtk.write('      </Cells>\n')

# footer
textoVtk.write('    </Piece>\n')
textoVtk.write('  </UnstructuredGrid>\n')
textoVtk.write('</VTKFile>\n')

textoVtk.close()



