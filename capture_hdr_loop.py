"""
Capture HDR frames in a loop (while actively changing some HDR settings).
"""

import zivid
import datetime


def _main():
    app = zivid.Application()

    print("Connecting to the camera")
    camera = app.connect_camera()

    print("Configuring the camera settings")
    settings_collection = [camera.settings for _ in range(3)]

    settings_collection[0].brightness = 1.8
    settings_collection[0].gain = 1
    settings_collection[0].filters.gaussian.enabled = True
    settings_collection[0].filters.gaussian.sigma = 1.5
    settings_collection[0].filters.reflection.enabled = True

    settings_collection[1].brightness = 1.8
    settings_collection[1].gain = 1
    settings_collection[1].filters.gaussian.enabled = True
    settings_collection[1].filters.gaussian.sigma = 1.5
    settings_collection[1].filters.reflection.enabled = True

    settings_collection[2].brightness = 1.8
    settings_collection[2].gain = 1.8
    settings_collection[2].filters.gaussian.enabled = True
    settings_collection[2].filters.gaussian.sigma = 1.5
    settings_collection[2].filters.reflection.enabled = True

    exposure_time_frame_1 = [
        datetime.timedelta(microseconds=10000),
        datetime.timedelta(microseconds=90000),
        datetime.timedelta(microseconds=40000),
    ]
    exposure_time_frame_2 = [
        datetime.timedelta(microseconds=40000),
        datetime.timedelta(microseconds=10000),
        datetime.timedelta(microseconds=90000),
    ]
    exposure_time_frame_3 = [
        datetime.timedelta(microseconds=90000),
        datetime.timedelta(microseconds=40000),
        datetime.timedelta(microseconds=10000),
    ]
    iris_frames = [10, 20, 30]

    for i in range(len(iris_frames)):
        settings_collection[0].exposure_time = exposure_time_frame_1[i]
        settings_collection[1].exposure_time = exposure_time_frame_2[i]
        settings_collection[2].exposure_time = exposure_time_frame_3[i]

        settings_collection[0].iris = iris_frames[i]
        settings_collection[1].iris = iris_frames[i]
        settings_collection[2].iris = iris_frames[i]

        print("Capturing an HDR frame")
        with camera.capture(settings_collection) as hdr_frame:
            print("Saving the HDR frame")
            hdr_frame.save("HDR.zdf")


if __name__ == "__main__":
    _main()
