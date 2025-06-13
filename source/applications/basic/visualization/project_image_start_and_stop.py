"""
Start the Image Projection and Stop it.

How to stop the image projection is demonstrated in three different ways:
- calling stop() function on the projected image handle
- projected image handle going out of scope
- triggering a 3D capture

"""

from typing import Tuple

import numpy as np
import zivid


def create_projector_image(resolution: Tuple, color: Tuple) -> np.ndarray:
    """Create projector image (numpy array) of given color.

    Args:
        resolution: projector resolution
        color: bgra

    Returns:
        An image (numpy array) of color given by the bgra value

    """
    projector_image = np.full((resolution[0], resolution[1], len(color)), color, dtype=np.uint8)
    return projector_image


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Retrieving the projector resolution that the camera supports")
    projector_resolution = zivid.projection.projector_resolution(camera)

    red_color = (0, 0, 255, 255)

    projector_image = create_projector_image(projector_resolution, red_color)

    project_image_handle = zivid.projection.show_image_bgra(camera, projector_image)

    input('Press enter to stop projecting using the ".stop()" function')
    project_image_handle.stop()

    green_color = (0, 255, 0, 255)
    projector_image = create_projector_image(projector_resolution, green_color)
    with zivid.projection.show_image_bgra(camera, projector_image):
        input("Press enter to stop projecting with context manager")

    pink_color = (114, 52, 237, 255)
    projector_image = create_projector_image(projector_resolution, pink_color)
    project_image_handle = zivid.projection.show_image_bgra(camera, projector_image)

    input("Press enter to stop projecting by performing a 3D capture")
    settings = zivid.Settings()
    settings.acquisitions.append(zivid.Settings.Acquisition())
    camera.capture_3d(settings)

    input("Press enter to exit")


if __name__ == "__main__":
    _main()
