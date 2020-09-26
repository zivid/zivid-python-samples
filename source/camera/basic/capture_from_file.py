"""File camera capture sample."""
import zivid


def _main():
    app = zivid.Application()
    camera = app.create_file_camera(str(zivid.environment.data_path()) + "/MiscObjects.zdf")

    with camera.capture() as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
