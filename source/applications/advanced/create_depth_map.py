"""
Import a ZDF point cloud and convert it to RGB image and Depth map in OpenCV format.
"""

from pathlib import Path
import numpy as np
import cv2
import zivid


def _main():

    app = zivid.Application()

    # The Zivid3D.zdf file has to be in the same folder as this sample script.
    filename_zdf = "Zivid3D.zdf"

    print(f"Reading {filename_zdf} point cloud")
    frame = zivid.Frame(Path() / f"{str(zivid.environment.data_path())}/{filename_zdf}")

    # Getting the point cloud
    point_cloud = frame.get_point_cloud().to_array()
    depth_map = np.dstack([point_cloud["z"]])

    depth_map_uint8 = (
        (depth_map - np.nanmin(depth_map)) / (np.nanmax(depth_map) - np.nanmin(depth_map)) * 255
    ).astype(np.uint8)

    # Applying color map
    depth_map_color_map = cv2.applyColorMap(depth_map_uint8, cv2.COLORMAP_JET)

    # Setting nans to black
    depth_map_color_map[np.isnan(depth_map)[:, :, 0]] = 0

    rgb = np.dstack([point_cloud["b"], point_cloud["g"], point_cloud["r"]])

    # Displaying the RGB image
    rgb_window = "ImageRGB"
    cv2.namedWindow(rgb_window, cv2.WINDOW_NORMAL)
    cv2.imshow(rgb_window, rgb)

    # Waiting for the window to be closed
    print("Close the RGB image to continue")
    while cv2.getWindowProperty(rgb_window, 0) >= 0:
        cv2.waitKey(50)
    cv2.destroyWindow(rgb_window)

    # Saving the RGB image
    cv2.imwrite(f"{rgb_window}.png", rgb)

    # Displaying the Depth map
    depth_window = "DepthMap"
    cv2.namedWindow(depth_window, cv2.WINDOW_NORMAL)
    cv2.imshow(depth_window, depth_map_color_map)

    # Waiting for the window to be closed
    print("Close the Depth map image to continue")
    while cv2.getWindowProperty(depth_window, 0) >= 0:
        cv2.waitKey(50)
    cv2.destroyWindow(depth_window)

    # Saving the Depth map
    cv2.imwrite(f"{depth_window}.png", depth_map_color_map)


if __name__ == "__main__":
    # If running the script from Spyder IDE, first run '%gui qt'
    _main()
