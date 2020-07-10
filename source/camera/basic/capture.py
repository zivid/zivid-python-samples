"""Capture sample."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    settings.acquisitions[0].aperture = 5.66
    settings.acquisitions[0].exposure_time = datetime.timedelta(microseconds=8333)

    with camera.capture(settings) as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
