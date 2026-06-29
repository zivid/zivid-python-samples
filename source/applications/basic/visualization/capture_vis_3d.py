"""
Capture point clouds, with color, from the Zivid camera, and visualize it.

For more information on visualization, check out this tutorial:
https://support.zivid.com/en/latest/camera/academy/applications/visualization-tutorial.html

"""

import zivid
import zivid.settings2d


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

    print("Visualizing point cloud")
    with zivid.visualization.Visualizer() as visualizer:
        visualizer.set_window_title("Zivid Point Cloud Visualizer")
        visualizer.colors_enabled = True
        visualizer.axis_indicator_enabled = True
        visualizer.show(frame)
        visualizer.reset_to_fit()
        visualizer.run()


if __name__ == "__main__":
    _main()
