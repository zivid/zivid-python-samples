""" 
Copyright (c) 2019, Zivid AS

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

3. Neither the name of Zivid AS nor the names of its contributors may
   be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY ZIVID AS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ZIVID AS OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""" 

""" 
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .PLY file format.

"""

import numpy as np
import struct
       
def write_ply_binary(fname, pts):
    
    with open(fname,'wb') as f:
        line = 'ply\n';
        f.write(line.encode('utf-8'))
        line = 'format binary_little_endian 1.0\n';
        f.write(line.encode('utf-8'))
        line = 'element vertex %d\n';
        f.write(line.encode('utf-8') % pts.shape[0])
        line = 'property float x\n';
        f.write(line.encode('utf-8'))
        line = 'property float y\n';
        f.write(line.encode('utf-8'))
        line = 'property float z\n';
        f.write(line.encode('utf-8'))
        line = 'property uchar red\n';
        f.write(line.encode('utf-8'))
        line = 'property uchar green\n';
        f.write(line.encode('utf-8'))
        line = 'property uchar blue\n';
        f.write(line.encode('utf-8'))
        line = 'end_header\n';
        f.write(line.encode('utf-8'))

        for i in range(len(pts)):
            
            s = struct.pack('<fffBBB', pts[i,0], pts[i,1], pts[i,2], np.uint8(pts[i,3]), np.uint8(pts[i,4]), np.uint8(pts[i,5]))
    
            f.write(s)

if __name__ == '__main__':
    
    from netCDF4 import Dataset
    
    # Read a .ZDF point cloud. The "Zivid3D.zdf" file has to be in the same folder
    # as the "SampleZDF2PLY" file.    
    FilenameZDF = 'Zivid3D.zdf'
    FilenamePLY = 'Zivid3D.ply'    
    data = Dataset(FilenameZDF)
    
    # Extract the point cloud
    xyz = data['data']['pointcloud'][:,:,:]
    
    # Extract the RGB image
    image = data['data']['rgba_image'][:,:,:3]
    
    # Close the ZDF file
    data.close()
    
    # Disorganize the point cloud
    pc = np.dstack([xyz, image])

    # Replace NaNs with Zeros
    pc[np.isnan(pc[:,:,2])] = 0;
    pts = pc.reshape(-1,6)
        
    # Save to a .PLY file format
    write_ply_binary(FilenamePLY, pts)