import os, re
import numpy as np
from osgeo import gdal
import flopy
from flopy.export import vtk as fv
import vtk
import flopy.utils.binaryfile as fpu
import flopy.utils.binaryfile as bf
import matplotlib.pyplot as plt

stp = 0
cbb = bf.CellBudgetFile('model1.cbc')
kstpkper_list = cbb.get_kstpkper()
text_list = cbb.textlist


frf = cbb.get_data(kstpkper=(0,stp),text=text_list[4])
drain_cbc = cbb.create3D(frf[0],1,cbb.nrow,cbb.ncol)
a=drain_cbc[0]
drain=a.filled()

drain_sum = np.sum(a)

CHD = cbb.get_data(kstpkper=(0,stp),text=text_list[0])
CHD_cbc = cbb.create3D(CHD[0],6,cbb.nrow,cbb.ncol)
a=CHD_cbc[0]
chead=a.filled()
chead[chead == 1e+20] = 0

chd_sum = np.sum(chead)

RCH = cbb.get_data(kstpkper=(0,stp),text=text_list[5])
rch = RCH[0][1]

rch_sum = np.sum(rch)

RF = cbb.get_data(kstpkper=(0,stp),text=text_list[1])
FF = cbb.get_data(kstpkper=(0,stp),text=text_list[2])
LF = cbb.get_data(kstpkper=(0,stp),text=text_list[3])
RF = RF[0]
FF = FF[0]
LF = LF[0]



RF_pad = np.lib.pad(RF, (1,1), 'constant', constant_values=0)
FF_pad = np.lib.pad(FF, (1,1), 'constant', constant_values=0)
LF_pad = np.lib.pad(LF, (1,1), 'constant', constant_values=0)
sum_flow = np.ones((cbb.nlay,RF.shape[1],RF.shape[2]))

for i in range (1,cbb.nlay+1):
    for j in range (1,RF.shape[1]+1):
        for k in range (1,RF.shape[2]+1):
            temp_sum=0
            if RF_pad[i,j,k-1]>0:
                temp_sum = temp_sum + np.abs(RF_pad[i,j,k-1])
            if RF_pad[i,j,k+1]<0:
                temp_sum = temp_sum + np.abs(RF_pad[i,j,k+1])
            if FF_pad[i,j-1,k]>0:
                temp_sum = temp_sum + np.abs(FF_pad[i,j-1,k])
            if FF_pad[i,j+1,k]<0:
                temp_sum = temp_sum + np.abs(FF_pad[i,j+1,k])
            if LF_pad[i+1,j,k]<0:
                temp_sum = temp_sum + np.abs(LF_pad[i+1,j,k])
            if LF_pad[i-1,j,k]>0:
                temp_sum = temp_sum + np.abs(LF_pad[i-1,j,k])

            sum_flow[i-1,j-1,k-1] = temp_sum


plt.figure()
plt.subplot(321)
plt.imshow(drain)
plt.colorbar()

plt.subplot(323)
plt.imshow(chead)
plt.colorbar()
plt.subplot(325)
plt.imshow(rch)
plt.colorbar()


plt.figure()
for i in range (0,cbb.nlay):
    plt.subplot(3,cbb.nlay,i+1)
    plt.imshow(RF[i],cmap='jet',vmin=-50, vmax=50)
    plt.colorbar()
    plt.subplot(3,cbb.nlay,i+(cbb.nlay+1))
    plt.imshow(FF[i],cmap='jet',vmin=-50, vmax=50)
    plt.colorbar()
    plt.subplot(3,cbb.nlay,i+(2*cbb.nlay)+1)
    plt.imshow(LF[i],cmap='jet',vmin=-50, vmax=50)
    plt.colorbar()

plt.figure()
plt.subplot(1,3,1)
plt.imshow(sum(RF),cmap='jet',vmin=-100, vmax=100)
plt.colorbar()
plt.subplot(1,3,2)
plt.imshow(sum(FF),cmap='jet',vmin=-100, vmax=100)
plt.colorbar()
plt.subplot(1,3,3)
plt.imshow(sum(LF),cmap='jet',vmin=-100, vmax=100)
plt.colorbar()

plt.figure()
for i in range (0,cbb.nlay):
    plt.subplot(1,6,1+i)
    plt.imshow(sum_flow[i],cmap='jet',vmin=0, vmax=50)
    plt.colorbar()

a = np.sum(sum(sum_flow))
plt.figure()
plt.imshow(sum(sum_flow),cmap='jet',vmin=-0, vmax=150)
plt.colorbar()


plt.show()
a=1
