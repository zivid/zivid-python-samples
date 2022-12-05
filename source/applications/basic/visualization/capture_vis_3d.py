"""
Capture point clouds, with color, from the Zivid camera, and visualize it.

"""

import zivid
from sample_utils.display import display_pointcloud


def _main() -> None:
    with zivid.Application() as app:

        print("Connecting to camera")
        camera = app.connect_camera()

        print("Configuring settings")
        settings = zivid.Settings()
        settings.acquisitions.append(zivid.Settings.Acquisition())
        settings.acquisitions[0].aperture = 5.66

        print("Capturing frame")
        with camera.capture(settings) as frame:

            point_cloud = frame.point_cloud()
            xyz = point_cloud.copy_data("xyz")
            rgba = point_cloud.copy_data("rgba")

            print("Visualizing point cloud")
            display_pointcloud(xyz, rgba[:, :, 0:3])


if __name__ == "__main__":
    _main()
