"""
This example shows how to capture 2D images from the Zivid camera.
"""

import datetime
import zivid


def _main():
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D settings")
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=30000)
    settings_2d.acquisitions[0].aperture = 11.31
    settings_2d.acquisitions[0].brightness = 1.80
    settings_2d.acquisitions[0].gain = 2.0
    settings_2d.processing.color.balance.red = 1.0
    settings_2d.processing.color.balance.green = 1.0
    settings_2d.processing.color.balance.blue = 1.0
    settings_2d.processing.color.gamma = 1.0

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        print("Getting RGBA image")
        image = frame_2d.image_rgba()
        rgba = image.copy_data()

        pixel_row = 100
        pixel_col = 50
        pixel = rgba[pixel_row, pixel_col]
        print(f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel[0]} G:{pixel[1]} B:{pixel[2]} A:{pixel[3]}")

        image_file = "Image.png"
        print(f"Saving image to file: {image_file}")
        image.save(image_file)


if __name__ == "__main__":
    _main()
