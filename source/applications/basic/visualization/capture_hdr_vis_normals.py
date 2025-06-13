"""
Capture Zivid point clouds, compute normals and convert to color map and display.

For scenes with high dynamic range we combine multiple acquisitions to get an HDR point cloud.

"""

import zivid
from zividsamples.display import display_pointcloud_with_downsampled_normals, display_rgb


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (5.66, 4.00, 2.83)],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame (HDR)")
    frame = camera.capture_2d_3d(settings)
    point_cloud = frame.point_cloud()
    rgba = point_cloud.copy_data("rgba_srgb")
    normals = point_cloud.copy_data("normals")
    normals_colormap = 0.5 * (1 - normals)

    print("Visualizing normals in 2D")
    display_rgb(rgb=rgba[:, :, :3], title="RGB image", block=False)
    display_rgb(rgb=normals_colormap, title="Colormapped normals", block=True)

    print("Visualizing normals in 3D")
    display_pointcloud_with_downsampled_normals(point_cloud, zivid.PointCloud.Downsampling.by4x4)


if __name__ == "__main__":
    _main()
