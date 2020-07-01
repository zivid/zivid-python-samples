"""HDR capture sample."""
import zivid


def _main():
    app = zivid.Application()
    camera = app.connect_camera()

    settings = zivid.Settings(
    acquisitions=[zivid.Settings.Acquisition(aperture=fnum) for fnum in (11.31, 5.66, 2.83)])

    with camera.capture(settings) as hdr_frame:
        hdr_frame.save("Result.zdf")


if __name__ == "__main__":
    _main()
