"""
Capture point clouds, with color, from the Zivid camera, and visualize it.

"""

import zivid
import zivid.settings2d
from zividsamples.display import display_pointcloud


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.acquisitions[0].aperture = 5.66
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings.color = settings_2d

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)

    point_cloud = frame.point_cloud()
    xyz = point_cloud.copy_data("xyz")
    rgba = point_cloud.copy_data("rgba_srgb")

    print("Visualizing point cloud")
    display_pointcloud(xyz, rgba[:, :, 0:3])


if __name__ == "__main__":
    _main()
