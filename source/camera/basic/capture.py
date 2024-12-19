"""
Capture colored point cloud, save 2D image, save 3D ZDF, and export PLY, using the Zivid camera.

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Creating default capture settings")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame")
    with camera.capture_2d_3d(settings) as frame:
        image_bgra = frame.frame_2d().image_rgba()
        image_file = "ImageRGBA.png"
        print(f"Saving 2D color image (linear RGB color space) to file: {image_file}")
        image_bgra.save(image_file)

        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)

        data_file_ply = "PointCloud.ply"
        print(f"Exporting point cloud to file: {data_file_ply}")
        frame.save(data_file_ply)


if __name__ == "__main__":
    _main()
