"""
Import ZDF point cloud and downsample it.
"""

import zivid
import numpy as np
from math import fmod
import matplotlib.pyplot as plt
from vtk_visualizer import plotxyzrgb

def downsample(x, y, z, image, contrast, dsf):
    # Function for downsampling a Zivid point cloud
    #
    # INPUT:
    # X - x data in a matrix
    # Y - y data in a matrix
    # Z - z data in a matrix
    # R - Red color band from color image (scaled from 0 to 1)
    # G - Green color band from color image (scaled from 0 to 1)
    # B - Blue color band from color image (scaled from 0 to 1)
    # Image - Color image (uint8 - 0 to 255)
    # Contrast - Contrast image / quality image (float)
    # dsf - Downsampling factor (values: 1,2,3,4,5,6) represents the
    # denominator of a fraction that represents the size of the downsampled
    # point cloud relative to the original point cloud, e.g. 2 - one-half,
    # 3 - one-third, 4 one-quarter, etc.
    #
    # OUTPUT:
    # pc_new - Downsampled Pointcloud (for use by pcshow and other MATLAB specific functions)
    # X_new - Downsampled x data in a matrix
    # Y_new - Downsampled y data in a matrix
    # Z_new - Downsampled z data in a matrix
    # R_new - Downsampled Red color band from color image (scaled from 0 to 1)
    # G_new - Downsampled Green color band from color image (scaled from 0 to 1)
    # B_new - Downsampled Blue color band from color image (scaled from 0 to 1)
    # Image_new - Downsampled Color image (uint8 - 0 to 255)
    
    # Checking if dsf is ok
    
    [h,w,d] = image.shape;
    
    if fmod(dsf,2) != 0 or  fmod(h,dsf) or  fmod(w,dsf):
        print("Downsampling factor - dsf has to have one of the following values: 2, 3, 4, 5, 6.")

#    # Downsampling by sum algorithm
#        b6 = image[:,:,i]
#        # Reshape and sum in first direction
#        b6b = np.transpose(b6)
#        
#        b5 = b6b.reshape(-1,dsf)
#        b5b= np.transpose(b5)
#        b4 = np.nansum(b5b,0)
#    
#        b3 = int(np.shape(b6b)[1]/dsf)
#        b2 = int(np.shape(b6b)[0])
#        b1 = b4.reshape(b2,b3)
#        b1b = np.transpose(b1)
#        b0 = (b1b)
#        k4 = b0
        
    sumline = lambda matrix,dsf : (np.transpose(np.nansum(np.transpose(np.transpose(matrix).reshape(-1,dsf)),0).reshape(int(np.shape(np.transpose(matrix))[0]),int(np.shape(np.transpose(matrix))[1]/dsf))))
#    # repeat for second direction
#    k4 = sumline(matrix,dsf)
#    k3 = np.transpose(k4)    
#    k2 = sumline(k3,dsf)    
#    k1 = np.transpose(k2)
#    k0 = (k1)
#    
    gridsum = lambda matrix,dsf : (sumline(np.transpose(sumline(matrix,dsf)),dsf));
        
    image_new = np.zeros((int(image.shape[0]/dsf), int(image.shape[1]/dsf), 3), dtype=np.uint8)
    
    for i in range(3):
        
#        k4 = sumline(image[:,:,i],dsf);
        
#        b6 = image[:,:,i]
#        # Reshape and sum in first direction
#        b6b = np.transpose(b6)
#        
#        b5 = b6b.reshape(-1,dsf)
#        b5b= np.transpose(b5)
#        b4 = np.nansum(b5b,0)
#    
#        b3 = int(np.shape(b6b)[1]/dsf)
#        b2 = int(np.shape(b6b)[0])
#        b1 = b4.reshape(b2,b3)
#        b1b = np.transpose(b1)
#        b0 = (b1b)
#        k4 = b0
        
#        k3 = np.transpose(k4)
#        
#        k2 = sumline(k3,dsf);
        
#        b6 = k3
#        b6b = np.transpose(b6)
#        b5 = b6b.reshape(-1,dsf)
#        b5b= np.transpose(b5)
#        b4 = np.nansum(b5b,0)
#    
#        b3 = int(np.shape(b6b)[1]/dsf)
#        b2 = int(np.shape(b6b)[0])
#        b1 = b4.reshape(b2,b3)
#        b1b = np.transpose(b1)
#        b0 = (b1b)
#        k2 = b0
        
#        k1 = np.transpose(k2)
        image_new[:,:,i] = ((np.transpose(gridsum(image[:,:,i],dsf)))/(dsf*dsf)).astype(np.uint8)

    #return x_new, y_new, z_new, image_new
    
    # Displaying the RGB image
    plt.figure()
    plt.imshow(image_new)
    plt.title("RGB image")
    plt.show()
    
        # Displaying the Depth Image
#    Z = xyz[:, :, 2]
#    plt.figure()
#    plt.imshow(Z, vmin=np.nanmin(Z), vmax=np.nanmax(Z), cmap="jet")
#    plt.colorbar()
#    plt.title("Depth map")
#    plt.show()
#
#    # Displaying the point cloud
#    plotxyzrgb(pts)
    
    return 1

def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    pc = frame.get_point_cloud()
    x = np.dstack([pc["x"]])
    y = np.dstack([pc["y"]])
    z = np.dstack([pc["z"]])
    rgb = np.dstack([pc["r"], pc["g"], pc["b"]])
    contrast = np.dstack([pc["contrast"]])
    #pc = np.dstack([xyz, rgb, contrast])

    # Flattening the point cloud
    #pts = pc.reshape(-1, 7)
    
    sad = downsample(x,y,z,rgb,contrast,4)


if __name__ == "__main__":
    _main()
    

