"""Capture sample."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    with camera.update_settings() as updater:
        updater.settings.iris = 20
        updater.settings.exposure_time = datetime.timedelta(microseconds=6500)
        updater.settings.filters.outlier.enabled(True)
        updater.settings.filters.outlier.threshold(5)

    with camera.capture() as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
