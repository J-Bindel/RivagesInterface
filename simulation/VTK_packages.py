# # Import packages, read files and create empty dicts

# In[1]:


import os, re
import numpy as np
from workFunctions import workFunctions
from vtkFunctions import vtkFunctions
from transFunctions import transFunctions
from listFunctions import listFunctions

# In[2]:


# open the DIS, BAS and FHD and DRN files
chdLines = open('../DEM/model1.chd').readlines()
disLines = open('../DEM/model1.dis').readlines()
drnLines = open('../DEM/model1.drn').readlines()
icLines = open('../DEM/model1.ic').readlines()
npfLines = open('../DEM/model1.npf').readlines()
rchLines = open('../DEM/model1.rch').readlines()
welLines = open('../DEM/model1.wel').readlines()

# In[3]:


# create a empty dictionay to store the model features
modChd = {}
modDis = {}
modDrn = {}
modIc = {}
modNpf = {}
modRch = {}
modWel = {}
modHds = {}

# <br/>
# <br/>
# <br/>
# ___
#
# # Working with the DIS (Discretization Data) data

# ### General model features as modDis dict

# In[4]:


########################
### General model features as modDis dict
# get the number of layers, rows, columns, cell and vertex numbers
for line in disLines:
    if 'NLAY' in line:
        modDis['cellLays'] = int(line.split()[1])
    elif 'NROW' in line:
        modDis['cellRows'] = int(line.split()[1])
    elif 'NCOL' in line:
        modDis['cellCols'] = int(line.split()[1])

modDis["vertexLays"] = modDis["cellLays"] + 1
modDis["vertexRows"] = modDis["cellRows"] + 1
modDis["vertexCols"] = modDis["cellCols"] + 1
modDis["vertexPerLay"] = modDis["vertexRows"] * modDis["vertexCols"]
modDis["cellsPerLay"] = modDis["cellRows"] * modDis["cellCols"]

########################
### Get the DIS Breakers
modDis['DELRArray1D'] = workFunctions.getListFromDel('DELR', modDis, disLines)
modDis['DELCArray1D'] = workFunctions.getListFromDel('DELC', modDis, disLines)

modDis['cellZVertexGrid'] = {}
modDis['cellZVertexGrid']['lay0'] = workFunctions.getUniLayerListFromTerm(modDis, disLines, 'TOP').reshape(
    modDis['cellRows'], modDis['cellCols'])

listFromBottom = workFunctions.getListinDictxLayFromGriddataLayered(modDis, disLines, 'BOTM', modDis)
# i = 0
for lay in range(1, modDis['vertexLays']):
    modDis['cellZVertexGrid']['lay' + str(lay)] = np.asarray(listFromBottom['lay' + str(lay - 1)]).reshape(
        modDis['cellRows'], modDis['cellCols'])
#    i+=1

########################
### Geolocation model data
modDis["vertexXmin"] = 0
modDis["vertexYmin"] = 0
modDis["vertexXmax"] = sum(modDis['DELRArray1D'])
modDis["vertexYmax"] = sum(modDis['DELCArray1D'])

########################
### List of arrays of cells and vertex coord
modDis['vertexEastingArray1D'] = np.array(
    [modDis['vertexXmin'] + np.sum(modDis['DELRArray1D'][:col]) for col in range(modDis['vertexCols'])])
modDis['vertexNorthingArray1D'] = np.array(
    [modDis['vertexYmax'] - np.sum(modDis['DELCArray1D'][:row]) for row in range(modDis['vertexRows'])])

modDis['cellEastingArray1D'] = np.array(
    [modDis['vertexXmin'] + np.sum(modDis['DELRArray1D'][:col]) + modDis['DELRArray1D'][col] / 2 for col in
     range(modDis['cellCols'])])
modDis['cellNorthingArray1D'] = np.array(
    [modDis['vertexYmax'] - np.sum(modDis['DELCArray1D'][:row]) - modDis['DELCArray1D'][row] / 2 for row in
     range(modDis['cellRows'])])

########################
### Grid of XYZ Vertex Coordinates
modDis['vertexXGrid'] = np.repeat(modDis['vertexEastingArray1D'].reshape(modDis['vertexCols'], 1), modDis['vertexRows'],
                                  axis=1).T
modDis['vertexYGrid'] = np.repeat(modDis['vertexNorthingArray1D'], modDis['vertexCols']).reshape(modDis['vertexRows'],
                                                                                                 modDis['vertexCols'])
modDis['vertexZGrid'] = transFunctions.interpolateCelltoVertex(modDis, 'cellZVertexGrid')

# <br/>
# <br/>
# <br/>
# ___
#
# # Get the Info for Boundary Conditions and Cell Heads

# In[5]:


# Get the NPF Info
modNpf['iCellTypeList'] = workFunctions.getListinDictxLayFromGriddataLayered(modNpf, npfLines, 'ICELLTYPE', modDis)
modNpf['kList'] = workFunctions.getListinDictxLayFromGriddataLayered(modNpf, npfLines, 'k LAYERED', modDis)
modNpf['K33List'] = workFunctions.getListinDictxLayFromGriddataLayered(modNpf, npfLines, 'K33 LAYERED', modDis)

# Get the IC Info
modIc['strtList'] = workFunctions.getListinDictxLayFromGriddataLayered(modIc, icLines, 'STRT', modDis)

# Get the DRN Info
modDrn['maxBound'] = workFunctions.getTermFromKeyword(drnLines, 'MAXBOUND', 'DIMENSIONS')
modDrn['drnCells'] = workFunctions.getCellsforBoundary(drnLines, 'drn', modDrn['maxBound'], 1)

# Get the CHD Info
modChd['maxBound'] = workFunctions.getTermFromKeyword(chdLines, 'MAXBOUND', 'DIMENSIONS')
modChd['chdCells'] = workFunctions.getCellsforBoundary(chdLines, 'chd', modChd['maxBound'], 1)

# Get the RCH Info
modRch['rchCellList'] = workFunctions.getUniLayerListFromTerm(modDis, rchLines, 'RECHARGE')

# Get the WEL Info
modWel['maxBound'] = workFunctions.getTermFromKeyword(welLines, 'MAXBOUND', 'DIMENSIONS')
modWel['welCells'] = workFunctions.getCellsforBoundary(welLines, 'wel', modWel['maxBound'], 1)

# Get the HDS info
### Store heads per lay
import flopy.utils.binaryfile as bf

modHds['cellHeadGrid'] = {}

headObject = bf.HeadFile('..\\model\\hatari01.hds', precision='double')
headObjectList = headObject.get_data()
headObject.close()

for lay in range(modDis['cellLays']):
    modHds['cellHeadGrid']['lay' + str(lay)] = headObjectList[lay]

vertexHeadGridCentroid = transFunctions.vertexHeadGridCentroidFunction(modDis, modHds)
modHds['vertexHeadGrid'] = transFunctions.vertexHeadGridFunction(vertexHeadGridCentroid, modDis, modHds)

# <br/>
# <br/>
# <br/>
# ___
#
# # VTK file of Model Geometry, Model Results and Boundary Conditions
#

# ## Point Data

# In[6]:


### Vertex Heads
listVertexHead = listFunctions.listCellHeadsFunction('vertexLays', 'vertexHeadGrid', modDis, modHds)

### Water Tables Vextex
listWaterTableVertex = listFunctions.listWaterTableVertexFunction(modDis, modHds)

# ## Point Definition

# In[7]:


### Definition of XYZ points for All Vertex
vertexXYZPoints = listFunctions.vertexXYZPointsFunction(modDis)

### Definition of XYZ points for Water Table
vertexWaterTableXYZPoints = listFunctions.vertexWaterTableXYZPointsFunction(listWaterTableVertex, modDis)

# ## Quad and Hexa Sequences

# In[8]:


### List of Layer Quad Sequences (Works only for a single layer)
listLayerQuadSequence = listFunctions.listLayerQuadSequenceFunction(modDis)

### List of Hexa Sequences for All Cells
listHexaSequence = listFunctions.listHexaSequenceFunction(modDis)

### List of Hexa Sequences for DRN Cells
listDrnCellsHexaSecuence = listFunctions.bcCellsListFunction(modDrn, 'drnCells', listHexaSequence, modDis)[1]

### List of Hexa Sequences for CHD Cells
listChdCellsHexaSecuence = listFunctions.bcCellsListFunction(modChd, 'chdCells', listHexaSequence, modDis)[1]

### List of Hexa Sequences for wEL Cells
listWelCellsHexaSecuence = listFunctions.bcCellsListFunction(modWel, 'welCells', listHexaSequence, modDis)[1]

# ## Cell Data

# In[9]:


### Definition of cellHead
listCellHead = listFunctions.listCellHeadsFunction('cellLays', 'cellHeadGrid', modDis, modHds)

### Definition of DRN cells values '1' as List
listDrnCellsIO = listFunctions.bcCellsListFunction(modDrn, 'drnCells', listHexaSequence, modDis)[0]

### Definition of CHD cells values '1' as List
listChdCellsIO = listFunctions.bcCellsListFunction(modChd, 'chdCells', listHexaSequence, modDis)[0]

### Definition of WEL cells values '1' as List
listWelCellsIO = listFunctions.bcCellsListFunction(modWel, 'welCells', listHexaSequence, modDis)[0]

### Water Tables on Cell
listWaterTableCell = listFunctions.listWaterTableCellFunction(modDis, modHds)

# <br/>
# <br/>
# <br/>
# ___
#
# # VTK Creation

# ## Heads on Vertex and Cells VTK

# In[10]:


vtkText = open('../vtuFiles/hatari01_Heads.vtu', 'w')

vtkFunctions.printHeader(vtkText, len(vertexXYZPoints), len(listHexaSequence))

vtkFunctions.printPointData(vtkText, 'VertexHeads', listVertexHead)

vtkFunctions.printCellData(vtkText, 'CellHeads', listCellHead)

vtkFunctions.printPointDefinition(vtkText, vertexXYZPoints)

vtkFunctions.printCellHexaConnectivityOffsetType(vtkText, listHexaSequence)

vtkFunctions.printFooter(vtkText)

vtkText.close()

# ## Water Table VTK

# In[11]:


vtkText = open('../vtuFiles/hatari01_WaterTable.vtu', 'w')

vtkFunctions.printHeader(vtkText, len(vertexWaterTableXYZPoints), len(listWaterTableCell))

vtkFunctions.printCellData(vtkText, 'WaterTableElev', listWaterTableCell)

vtkFunctions.printPointDefinition(vtkText, vertexWaterTableXYZPoints)

vtkFunctions.printCellQuadConnectivityOffsetType(vtkText, listLayerQuadSequence)

vtkFunctions.printFooter(vtkText)

vtkText.close()

# ## DRN Package VTK

# In[12]:


vtkText = open('../vtuFiles/hatari01_DRNCells.vtu', 'w')

vtkFunctions.printHeader(vtkText, len(vertexXYZPoints), len(listDrnCellsHexaSecuence))

vtkFunctions.printCellData(vtkText, 'DRNCells', listDrnCellsIO)

vtkFunctions.printPointDefinition(vtkText, vertexXYZPoints)

vtkFunctions.printCellHexaConnectivityOffsetType(vtkText, listDrnCellsHexaSecuence)

vtkFunctions.printFooter(vtkText)

vtkText.close()

# ## CHD Package VTK

# In[13]:


vtkText = open('../vtuFiles/hatari01_CHDCells.vtu', 'w')

vtkFunctions.printHeader(vtkText, len(vertexXYZPoints), len(listChdCellsHexaSecuence))

vtkFunctions.printCellData(vtkText, 'CHDCells', listChdCellsIO)

vtkFunctions.printPointDefinition(vtkText, vertexXYZPoints)

vtkFunctions.printCellHexaConnectivityOffsetType(vtkText, listChdCellsHexaSecuence)

vtkFunctions.printFooter(vtkText)

vtkText.close()

# ## WEL Package VTK

# In[14]:


vtkText = open('../vtuFiles/hatari01_WELCells.vtu', 'w')

vtkFunctions.printHeader(vtkText, len(vertexXYZPoints), len(listWelCellsHexaSecuence))

vtkFunctions.printCellData(vtkText, 'WELCells', listWelCellsIO)

vtkFunctions.printPointDefinition(vtkText, vertexXYZPoints)

vtkFunctions.printCellHexaConnectivityOffsetType(vtkText, listWelCellsHexaSecuence)

vtkFunctions.printFooter(vtkText)

vtkText.close()