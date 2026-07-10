"""
Demonstrate zero-copy GPU interop between Zivid and PyTorch/CuPy by feeding a Zivid 2D image into a third-party
segmentation model without a CPU round-trip.

DISCLAIMER: Zivid does not provide segmentation, and Zivid does not support the third-party libraries used in this
sample. The segmentation model (DeepLabV3 from torchvision) and the GPU interop libraries (PyTorch, CuPy) are external
dependencies that the user is responsible for installing, configuring, and maintaining. This sample exists solely to
demonstrate how to pass Zivid GPU data to an external consumer without copying it through CPU memory.

Only the handoff is zero-copy: Zivid produces the image on the GPU as a DeviceArray, CuPy wraps that GPU memory as an
ndarray, and PyTorch consumes the CuPy array via DLPack -- no CPU round-trip. The model's preprocessing, inference, and
output (`predictions`, `predictions_resized`) allocate new GPU buffers as usual, and `predictions.cpu().numpy()` at the
end copies the result to CPU for visualization. In a real pipeline you would keep results on the GPU. See the related
samples `capture_and_process_image_with_cupy_on_cuda.py` and `capture_and_render_point_cloud_with_opengl_on_cuda.py`
for other ways to consume Zivid GPU data without a CPU round-trip.

Requirements:
- CUDA-capable GPU
- PyTorch with CUDA support: pip install torch torchvision
- CuPy for zero-copy GPU interop: pip install cupy-cuda12x

"""

from typing import List, Tuple

import cv2
import numpy as np
import zivid


def _print_disclaimer(lines: List[str]) -> None:
    width = max(len(line) for line in lines) + 4
    border = "#" * width
    print()
    print(border)
    for line in lines:
        print(f"# {line.ljust(width - 4)} #")
    print(border)
    print()


try:
    import torch
    from torchvision.models.segmentation import DeepLabV3_MobileNet_V3_Large_Weights, deeplabv3_mobilenet_v3_large
except ImportError:
    print("⚠️  Failed to import PyTorch and torchvision. They are installed via `pip install torch torchvision`.")
    raise

try:
    import cupy as cp
except ImportError:
    print("⚠️  Failed to import CuPy. It is installed via `pip install cupy-cuda12x` (adjust for your CUDA version).")
    raise


def _create_color_palette(num_classes: int) -> np.ndarray:
    """Create a color palette for visualizing segmentation classes.

    Args:
        num_classes: Number of segmentation classes.

    Returns:
        Color palette as numpy array with shape (num_classes, 3).

    """
    palette = np.zeros((num_classes, 3), dtype=np.uint8)
    for i in range(num_classes):
        r = (i * 100) % 256
        g = (i * 150 + 50) % 256
        b = (i * 200 + 100) % 256
        palette[i] = [r, g, b]
    return palette


def _initialize_pytorch_cuda() -> torch.device:
    """Initialize PyTorch CUDA and return the device.

    Returns:
        PyTorch CUDA device.

    Raises:
        RuntimeError: If PyTorch CUDA is not available.

    """
    if not torch.cuda.is_available():
        raise RuntimeError("PyTorch CUDA is not available")

    torch_device = torch.device("cuda")
    print(f"PyTorch CUDA device: {torch.cuda.get_device_name()}")

    # Force CUDA initialization by creating a small tensor
    torch.zeros(1, device=torch_device)

    return torch_device


def _load_segmentation_model(torch_device: torch.device) -> torch.nn.Module:
    """Load and prepare the DeepLabV3 segmentation model.

    Args:
        torch_device: PyTorch device to load the model on.

    Returns:
        Loaded segmentation model in eval mode.

    """
    print("Loading DeepLabV3 segmentation model")
    weights = DeepLabV3_MobileNet_V3_Large_Weights.DEFAULT
    model = deeplabv3_mobilenet_v3_large(weights=weights)
    model = model.to(torch_device)
    model.eval()
    return model


def _run_segmentation(
    model: torch.nn.Module,
    torch_image: torch.Tensor,
    torch_device: torch.device,
    original_size: Tuple[int, int],
) -> torch.Tensor:
    """Run segmentation inference on the input image.

    Args:
        model: Segmentation model.
        torch_image: Input image tensor in HWC format with values in [0, 1].
        torch_device: PyTorch device.
        original_size: Original image size (height, width) for resizing output.

    Returns:
        Segmentation mask tensor resized to original size.

    """
    # Rearrange to CHW format and normalize for the model
    torch_image = torch_image.permute(2, 0, 1).clamp(0, 1)

    # Resize for model (DeepLabV3 works best with specific sizes)
    model_size = (520, 520)
    torch_image_resized = torch.nn.functional.interpolate(
        torch_image.unsqueeze(0), size=model_size, mode="bilinear", align_corners=False
    )

    # Apply model preprocessing (normalization)
    mean = torch.tensor([0.485, 0.456, 0.406], device=torch_device).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225], device=torch_device).view(1, 3, 1, 1)
    torch_image_normalized = (torch_image_resized - mean) / std

    # Run inference
    print("Running segmentation inference on GPU")
    with torch.no_grad():
        output = model(torch_image_normalized)["out"]

    # Get class predictions and resize to original size
    predictions = output.argmax(1).squeeze(0)
    predictions_resized = (
        torch.nn.functional.interpolate(
            predictions.float().unsqueeze(0).unsqueeze(0),
            size=original_size,
            mode="nearest",
        )
        .squeeze()
        .byte()
    )

    print(f"Segmentation output shape: {predictions_resized.shape}")
    print(f"Unique classes detected: {torch.unique(predictions_resized).cpu().numpy()}")

    return predictions_resized


def _visualize_and_save(segmentation_mask: np.ndarray, original_rgb: np.ndarray, width: int, height: int) -> None:
    """Visualize segmentation results and save to file.

    Args:
        segmentation_mask: Segmentation mask as numpy array.
        original_rgb: Original RGB image as numpy array.
        width: Original image width.
        height: Original image height.

    """
    original_bgr = cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR)

    # Create colored segmentation visualization
    num_classes = 21  # PASCAL VOC classes
    palette = _create_color_palette(num_classes)
    segmentation_colored = palette[segmentation_mask]

    # Blend original image with segmentation
    blended = cv2.addWeighted(original_bgr, 0.5, segmentation_colored, 0.5, 0)

    # Resize for display
    display_width = 800
    scale = display_width / width
    display_size = (display_width, int(height * scale))

    original_display = cv2.resize(original_bgr, display_size)
    segmentation_display = cv2.resize(segmentation_colored, display_size)
    blended_display = cv2.resize(blended, display_size)

    # Stack images and add labels
    combined_display = np.hstack([original_display, segmentation_display, blended_display])
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(combined_display, "Original", (10, 30), font, 1, (0, 255, 0), 2)
    cv2.putText(combined_display, "Segmentation", (display_width + 10, 30), font, 1, (0, 255, 0), 2)
    cv2.putText(combined_display, "Blended", (2 * display_width + 10, 30), font, 1, (0, 255, 0), 2)

    # Display and save
    cv2.imshow("GPU Interop Demo (third-party segmentation model)", combined_display)
    print("Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imwrite("gpu_segmentation_result.png", combined_display)
    print("Saved result to gpu_segmentation_result.png")


def _main() -> None:
    _print_disclaimer(
        [
            "DISCLAIMER",
            "",
            "This sample demonstrates ZERO-COPY GPU INTEROP between Zivid and PyTorch.",
            "The segmentation model is a THIRD-PARTY component NOT provided or supported by Zivid.",
            "The model is NOT expected to produce MEANINGFUL segmentation results.",
            "It is included ONLY to show how to pass GPU data to an external consumer.",
        ]
    )

    torch_device = _initialize_pytorch_cuda()

    print("Initializing Zivid application (will reuse PyTorch's CUDA context)")
    app = zivid.Application()

    print("Verifying that CUDA backend is available")
    compute_device = app.compute_device()
    if compute_device.backend != zivid.ComputeBackend.cuda:
        raise RuntimeError("This sample requires CUDA backend")
    print(f"Using GPU: {compute_device.model}")

    _print_disclaimer(
        [
            "DISCLAIMER",
            "",
            "Loading THIRD-PARTY segmentation model (DeepLabV3 from torchvision).",
            "This model is NOT part of the Zivid SDK and is used here ONLY to illustrate GPU interop.",
        ]
    )
    model = _load_segmentation_model(torch_device)

    print("Connecting to camera")
    camera = app.connect_camera()
    settings_2d = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])

    print("Capturing 2D frame")
    frame_2d = camera.capture_2d(settings_2d)

    print("Creating a PyTorch CUDA stream for GPU operations")
    pytorch_stream = torch.cuda.Stream()
    print(f"Using CUDA stream: {hex(pytorch_stream.cuda_stream)}")

    print("Getting GPU device buffer in float format (RGBAf32), synchronized into the PyTorch stream")
    # The DeviceArray is synchronized into zivid_stream at acquisition (via events,
    # non-blocking), so consuming it on the same stream below needs no extra synchronization.
    zivid_stream = zivid.CUDAStreamPtr(pytorch_stream.cuda_stream)
    device_array = frame_2d.image_device_array(zivid_stream, zivid.PixelFormat.RGBAF)
    height = device_array.shape[0]
    width = device_array.shape[1]
    print(f"Image size: {width}x{height}")

    print("Wrapping the stream for CuPy operations")
    cupy_stream = cp.cuda.ExternalStream(pytorch_stream.cuda_stream)

    print("Running all GPU operations on the shared stream")
    with torch.cuda.stream(pytorch_stream), cupy_stream:
        print("Wrapping device buffer as a CuPy array (this is the zero-copy step; Zivid still owns the memory)")
        cupy_rgba = cp.asarray(device_array)

        print("Extracting RGB channels and transferring to PyTorch via DLPack (zero-copy)")
        cupy_rgb = cp.ascontiguousarray(cupy_rgba[:, :, :3])
        torch_image = torch.from_dlpack(cupy_rgb)
        print(f"PyTorch tensor shape: {torch_image.shape}, dtype: {torch_image.dtype}")

        _print_disclaimer(
            [
                "DISCLAIMER",
                "",
                "The segmentation model is NOT expected to produce MEANINGFUL results.",
                "It is a generic model NOT trained for industrial 3D camera images.",
                "The output is included ONLY to demonstrate the GPU interop pipeline.",
            ]
        )
        predictions_resized = _run_segmentation(model, torch_image, torch_device, (height, width))

        print("Moving result GPU -> CPU for visualization (in a real pipeline you would keep this on the GPU)")
        segmentation_mask = predictions_resized.cpu().numpy()
        original_rgb = (cupy_rgb.get() * 255).astype(np.uint8)

    _visualize_and_save(segmentation_mask, original_rgb, width, height)


if __name__ == "__main__":
    _main()
