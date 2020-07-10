"""Capture sample."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    settings = zivid.Settings(
        acquisitions=[
            zivid.Settings.Acquisition(aperture=5.66, exposure_time=datetime.timedelta(microseconds=8333),),
        ],
    )

    with camera.capture(settings) as frame:
        frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
