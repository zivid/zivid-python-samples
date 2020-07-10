"""Capture sample 2D."""
import datetime
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    settings_2d = zivid.Settings2D(
        acquisitions=[
            zivid.Settings2D.Acquisition(aperture=2.83, exposure_time=datetime.timedelta(microseconds=10000),)
        ],
    )

    with camera.capture(settings_2d) as frame_2d:
        image = frame_2d.image_rgba()
        image.save("Result.png")


if __name__ == "__main__":
    _main()
