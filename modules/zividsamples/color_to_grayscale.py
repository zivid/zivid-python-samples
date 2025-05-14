import numpy as np


def convert_rgba_to_grayscale(rgba_image: np.ndarray) -> np.ndarray:
    """Convert RGBA image to grayscale using the luminance method.

    The luminance method uses the formula:
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    where R, G, B are the red, green, and blue channels of the image.
    The alpha channel is ignored in this conversion.

    Args:
        rgba_image (numpy.ndarray): Input RGBA image.

    Raises:
        ValueError: If the input image is not a RGBA image.

    Returns:
        numpy.ndarray: Grayscale image.
    """
    if rgba_image.ndim != 3 or rgba_image.shape[2] != 4:
        raise ValueError("Input image must be a RGBA image.")
    return np.dot(rgba_image[..., :3], [0.299, 0.587, 0.114])


def convert_bgra_to_grayscale(bgra_image: np.ndarray) -> np.ndarray:
    """Convert BGRA image to grayscale using the luminance method.

    The luminance method uses the formula:
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    where R, G, B are the red, green, and blue channels of the image.

    Args:
        bgra_image (numpy.ndarray): Input BGRA image.

    Raises:
        ValueError: If the input image is not a BGRA image.

    Returns:
        numpy.ndarray: Grayscale image.
    """
    if bgra_image.ndim != 3 or bgra_image.shape[2] != 4:
        raise ValueError("Input image must be a BGRA image.")
    return np.dot(bgra_image[..., :3], [0.114, 0.587, 0.299])
