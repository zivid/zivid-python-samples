"""
Capture 2D images from the Zivid camera.

The color information is provided in linear RGB and sRGB color spaces.

Color represented in linear RGB space is suitable as input to traditional computer vision algorithms
for specialized tasks that require precise color measurements or high dynamic range.

Color represented in sRGB color space is suitable for showing an image on a display and for machine
learning based tasks like image classification, object detection, and segmentation as most image
datasets used for training neural networks are in sRGB color space.

More information about linear RGB and sRGB color spaces is available at:
https://support.zivid.com/en/latest/reference-articles/color-spaces-and-output-formats.html#color-spaces

Note: While the data of the saved images is provided in linear RGB and sRGB color space, the meta data
information that indicates the color space is not saved in the .PNG. Hence, both images are likely
to be interpreted as if they were saved in sRGB color space and displayed as such.

"""

import datetime

import zivid


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring 2D settings")
    # Note: The Zivid SDK supports 2D captures with a single acquisition only
    settings_2d = zivid.Settings2D()
    settings_2d.acquisitions.append(zivid.Settings2D.Acquisition())
    settings_2d.acquisitions[0].exposure_time = datetime.timedelta(microseconds=20000)
    settings_2d.acquisitions[0].aperture = 9.51
    settings_2d.acquisitions[0].brightness = 1.80
    settings_2d.acquisitions[0].gain = 2.0
    settings_2d.processing.color.balance.red = 1.0
    settings_2d.processing.color.balance.green = 1.0
    settings_2d.processing.color.balance.blue = 1.0
    settings_2d.processing.color.gamma = 1.0

    print("Capturing 2D frame")
    with camera.capture(settings_2d) as frame_2d:
        print("Getting color image (linear RGB color space)")
        image = frame_2d.image_rgba()
        rgba = image.copy_data()

        pixel_row = 100
        pixel_col = 50
        pixel = rgba[pixel_row, pixel_col]
        print(f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel[0]} G:{pixel[1]} B:{pixel[2]} A:{pixel[3]}")

        image_file = "ImageRGB.png"
        print(f"Saving 2D color image (linear RGB color space) to file: {image_file}")
        image.save(image_file)

        print("Getting color image (sRGB color space)")
        image_srgb = frame_2d.image_srgb()
        srgb = image_srgb.copy_data()

        pixel = srgb[pixel_row, pixel_col]
        print(f"Color at pixel ({pixel_row},{pixel_col}): R:{pixel[0]} G:{pixel[1]} B:{pixel[2]} A:{pixel[3]}")

        image_srgb_file = "ImageSRGB.png"
        print(f"Saving 2D color image  (sRGB color space) to file: {image_srgb_file}")
        image_srgb.save(image_srgb_file)


if __name__ == "__main__":
    _main()
