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
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings.color = settings_2d

    print("Capturing frame")
    frame = camera.capture_2d_3d(settings)

    point_cloud = frame.point_cloud()

    print("Visualizing point cloud")
    display_pointcloud(point_cloud)


if __name__ == "__main__":
    _main()
