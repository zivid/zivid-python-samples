"""
This example shows how to import a Zivid point cloud from a .ZDF file.
"""

from netCDF4 import Dataset
from matplotlib import pyplot as plt
import numpy

# Read a .ZDF point cloud. The "Zivid3D.zdf" file has to be in the same folder
# as the "SampleReadZDF" file.
FilenameZDF = "Zivid3D.zdf"
data = Dataset(FilenameZDF, "r")

# Extract the point cloud
pc = data["data"]["pointcloud"][:, :, :]

# Extract the RGB image
image = data["data"]["rgba_image"][:, :, :]

# Extract the contrast image
contrast = data["data"]["contrast"][:, :]

# Close the ZDF file
data.close()

# Display the RGB image
plt.imshow(image)
plt.show()

# Display the Depth Image
Z = pc[:, :, 2]
plt.imshow(Z, vmin=numpy.nanmin(Z), vmax=numpy.nanmax(Z), cmap="jet")
plt.colorbar()
plt.show()
