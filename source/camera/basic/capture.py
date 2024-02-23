"""
Capture point clouds, with color, from the Zivid camera.

"""

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Creating default capture settings")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())

    print("Capturing frame")
    with camera.capture(settings) as frame:
        data_file = "Frame.zdf"
        print(f"Saving frame to file: {data_file}")
        frame.save(data_file)

        data_file_ply = "PointCloud.ply"
        print(f"Exporting point cloud to file: {data_file_ply}")
        frame.save(data_file_ply)


if __name__ == "__main__":
    _main()
