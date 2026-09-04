"""
Demonstrate GPU interop with CuPy: wrap a Zivid GPU image buffer as a CuPy array without copying it through CPU memory.

Only the handoff from Zivid to CuPy is zero-copy. CuPy operations afterwards (e.g. `arr * 1.2`, `.astype(...)`) allocate
new GPU buffers as usual, and `cp.asnumpy(...)` at the end copies to CPU for display. In a real pipeline you would keep
results on the GPU and pass them straight to the next consumer (PyTorch, OpenGL, a CUDA kernel, etc.) -- see the related
samples `capture_and_segment_image_with_pytorch_on_cuda.py` and `capture_and_render_point_cloud_with_opengl_on_cuda.py`.

zivid-python implements `__cuda_array_interface__` on DeviceArray, so `cp.asarray(device_array)` is the whole handoff:
CuPy picks up the device pointer, dtype, shape and strides, and holds the DeviceArray as the buffer's owner. Avoid
building the array from `cp.cuda.UnownedMemory` with something else passed as `owner` -- the buffer belongs to the
DeviceArray, not to the frame or point cloud it came from, and getting that wrong frees GPU memory that CuPy still
points at.

Requirements:
- CUDA-capable GPU
- CuPy installed: pip install cupy-cuda12x (adjust for your CUDA version)

"""

import zivid
from zividsamples.display import display_rgbs

# CuPy import - this sample requires CuPy to be installed
try:
    import cupy as cp
except ImportError:
    print("⚠️  Failed to import CuPy. It is installed via `pip install cupy-cuda12x` (adjust for your CUDA version).")
    raise


def _main() -> None:
    app = zivid.Application()

    print("Verifying that CUDA backend is available")
    compute_device = app.compute_device()
    if compute_device.backend != zivid.ComputeBackend.cuda:
        raise RuntimeError("This sample requires CUDA backend")

    print(f"Using GPU: {compute_device.model}")

    print("Connecting to camera")
    camera = app.connect_camera()

    print("Configuring settings")
    settings_2d = zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()])

    print("Capturing 2D frame")
    frame_2d = camera.capture_2d(settings_2d)

    # Use default CUDA stream for synchronization (simplest approach)
    # For async processing, you can create a custom stream:
    #   cupy_stream = cp.cuda.Stream(non_blocking=True)
    #   cuda_stream = zivid.CUDAStreamPtr(cupy_stream.ptr)
    cuda_stream = zivid.CUDAStreamPtr()  # Default stream

    print("Getting GPU device buffer in float format (RGBAf32)")
    # The DeviceArray is synchronized into cuda_stream at acquisition, so it can be handed
    # to CuPy directly without any further synchronization.
    device_array = frame_2d.image_device_array(cuda_stream, zivid.PixelFormat.RGBAF)

    print(f"Device pointer: {hex(device_array.device_pointer())}")
    print(
        f"Buffer: {device_array.shape[1]}x{device_array.shape[0]}, "
        f"stride={device_array.strides_in_bytes[0]} bytes, total size={device_array.size_bytes} bytes"
    )

    print("Wrapping Zivid's GPU buffer as a CuPy array (this is the zero-copy step; Zivid still owns the memory)")
    print("cp.asarray reads __cuda_array_interface__, so shape, dtype and strides come across automatically,")
    print("and CuPy holds the DeviceArray as the buffer's owner so the GPU memory cannot be freed too early")
    image_array = cp.asarray(device_array)

    print(f"CuPy array shape: {image_array.shape}")
    print(f"CuPy array dtype: {image_array.dtype}")

    if image_array.data.ptr != device_array.device_pointer():
        raise RuntimeError("Zero-copy check failed: CuPy array does not share the Zivid device pointer")
    print("Zero-copy verified: CuPy array shares the Zivid device pointer")

    print("Example: Computing mean color on GPU")
    mean_rgba = cp.mean(image_array, axis=(0, 1))
    print(f"Mean RGBA values: R={mean_rgba[0]:.3f}, G={mean_rgba[1]:.3f}, B={mean_rgba[2]:.3f}, A={mean_rgba[3]:.3f}")

    print("Example: Increasing image brightness on GPU (allocates a new GPU buffer for the result)")
    brightened = cp.clip(image_array * 1.2, 0.0, 1.0)
    print("Applied brightness adjustment on GPU")

    print("Converting RGBAf32 to RGBA8 (0-255) for visualization")
    original_image_gpu = (image_array * 255).astype("uint8")
    brightened_image_gpu = (brightened * 255).astype("uint8")

    print("Copying result GPU -> CPU for display (in a real pipeline you would keep this on the GPU)")
    original_image_cpu = cp.asnumpy(original_image_gpu)
    brightened_image_cpu = cp.asnumpy(brightened_image_gpu)
    print(
        f"Copied to CPU array: original shape={original_image_cpu.shape}, brightened shape={brightened_image_cpu.shape}"
    )

    print("Displaying original and brightened images")
    display_rgbs([original_image_cpu, brightened_image_cpu], ["original", "brightened"], layout=(1, 2))


if __name__ == "__main__":
    _main()
