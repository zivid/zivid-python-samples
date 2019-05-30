""" 
BSD 3-Clause License

Copyright (c) 2019, Zivid AS
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

""" 
This example shows how to convert a Zivid point cloud from a .ZDF file format
to a .CSV file format.

"""

import numpy as np
from netCDF4 import Dataset
from math import ceil

# Read a .ZDF point cloud. The "Zivid3D.zdf" file has to be in the same folder
# as the "SampleZDF2CSV" file.
FilenameZDF = "Zivid3D.zdf"
FilenameTXT = "Zivid3D.txt"
data = Dataset(FilenameZDF)

# Extract the point cloud
xyz = data["data"]["pointcloud"][:, :, :]

# Extract the RGB image
image = data["data"]["rgba_image"][:, :, :3]

# Extract the contrast image
contrast = data["data"]["contrast"][:, :]

# Close the ZDF file
data.close()

# Disorganize the point cloud
pc = np.dstack([xyz, image, contrast])
pts = pc.reshape(-1, 7)
# Just points without color and contrast
# pc = np.dstack([xyz])
# pts = pc.reshape(-1,3)

# Remove nans
pts = pts[~np.isnan(pts[:, 0]), :]

# Save to a .TXT file format
parts = ceil(len(pts) / 1000000)
np.savetxt(FilenameTXT, pts, delimiter=" ", fmt="%.3f")
if parts > 1:
    for x in range(0, parts):
        index = FilenameTXT.find(".")
        Filename = FilenameTXT[:index] + "_part_" + str(x + 1) + FilenameTXT[index:]
        np.savetxt(
            Filename, pts[x * 1000000 : (x + 1) * 1000000, :], delimiter=" ", fmt="%.3f"
        )
