"""Capture sample 2D."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    settings_2d = zivid.Settings2D()
    settings_2d.iris = 20
    settings_2d.exposure_time = datetime.timedelta(microseconds=30000)
    settings_2d.brightness(1.8)
    settings_2d.gain(2.0)

    with camera.capture_2d(settings_2d) as frame_2d:
        image = frame_2d.image()
        image.save("Result.png")


if __name__ == "__main__":
    _main()
