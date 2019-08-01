"""
Import ZDF point cloud and downsample it.
"""

from math import fmod
import numpy as np
import matplotlib.pyplot as plt
import zivid
from vtk_visualizer import plotxyzrgb


def gridsum(matrix, downsampling_factor):
    """
    Reshape and sum in second direction
    """
    return sumline(
        np.transpose(sumline(matrix, downsampling_factor)), downsampling_factor
    )


def sumline(matrix, downsampling_factor):
    """
    Reshape and sum in first direction
    """
    return np.transpose(
        np.nansum(
            np.transpose(np.transpose(matrix).reshape(-1, downsampling_factor)), 0
        ).reshape(
            int(np.shape(np.transpose(matrix))[0]),
            int(np.shape(np.transpose(matrix))[1] / downsampling_factor),
        )
    )


def downsample(xyz, rgb, contrast, downsampling_factor):
    """
    Function for downsampling a Zivid point cloud    
    INPUT:
    xyz - point cloud
    image - color image
    contrast - contrast image
    downsampling_factor - (values: 2,3,4,5,6) the denominator of a
    fraction that represents the size of the downsampled point cloud relative
    to the original point cloud, e.g. 2 - one-half, 3 - one-third,
    4 one-quarter, etc.    
    OUTPUT:
    xyz_new - Downsampled point cloud
    image_new - Downsampled color image
    """

    # Checking if downsampling_factor is ok
    [height, width, dimension] = rgb.shape

    if (
        fmod(downsampling_factor, 2) != 0
        or fmod(height, downsampling_factor)
        or fmod(width, downsampling_factor)
    ):
        raise ValueError(
            "Downsampling factor - downsampling_factor has to have one of the following values: 2, 3, 4, 5, 6."
        )

    rgb_new = np.zeros(
        (
            int(rgb.shape[0] / downsampling_factor),
            int(rgb.shape[1] / downsampling_factor),
            3,
        ),
        dtype=np.uint8,
    )
    for i in range(3):
        rgb_new[:, :, i] = (
            (np.transpose(gridsum(rgb[:, :, i], downsampling_factor)))
            / (downsampling_factor * downsampling_factor)
        ).astype(np.uint8)

    contrast[np.isnan(xyz[:, :, 2])] = 0
    contrast_weight = gridsum(contrast[:, :, 0], downsampling_factor)

    x_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)
    y_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)
    z_initial = np.zeros((int(xyz.shape[0]), int(xyz.shape[1]), 1), dtype=np.float32)

    x_initial[:, :, 0] = xyz[:, :, 0]
    y_initial[:, :, 0] = xyz[:, :, 1]
    z_initial[:, :, 0] = xyz[:, :, 2]

    x_new = np.transpose(
        np.divide(
            gridsum((np.multiply(x_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )
    y_new = np.transpose(
        np.divide(
            gridsum((np.multiply(y_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )
    z_new = np.transpose(
        np.divide(
            gridsum((np.multiply(z_initial, contrast))[:, :, 0], downsampling_factor),
            contrast_weight,
        )
    )

    xyz_new = np.dstack([x_new, y_new, z_new])

    return xyz_new, rgb_new


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(filename_zdf)

    # Getting the point cloud
    point_cloud = frame.get_point_cloud()
    xyz = np.dstack([point_cloud["x"], point_cloud["y"], point_cloud["z"]])
    rgb = np.dstack([point_cloud["r"], point_cloud["g"], point_cloud["b"]])
    contrast = np.dstack([point_cloud["contrast"]])

    # Downsampling the point cloud
    downsampling_factor = 4
    [xyz_new, rgb_new] = downsample(xyz, rgb, contrast, downsampling_factor)

    # Getting the point cloud
    point_cloud = np.dstack([xyz_new, rgb_new])

    # Flattening the point cloud
    flattened_point_cloud = point_cloud.reshape(-1, 6)

    # Displaying the RGB image
    plt.figure()
    plt.imshow(rgb_new)
    plt.title("RGB image")
    plt.show()

    # Displaying the Depth map
    plt.figure()
    plt.imshow(
        xyz_new[:, :, 2],
        vmin=np.nanmin(xyz_new[:, :, 2]),
        vmax=np.nanmax(xyz_new[:, :, 2]),
        cmap="jet",
    )
    plt.colorbar()
    plt.title("Depth map")
    plt.show()

    # Displaying the point cloud
    plotxyzrgb(flattened_point_cloud)


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
    input("Press Enter to close...")
