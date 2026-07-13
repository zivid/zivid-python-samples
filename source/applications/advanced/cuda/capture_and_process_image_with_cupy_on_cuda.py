"""
Demonstrate GPU interop with CuPy: wrap a Zivid GPU image buffer as a CuPy array without copying it through CPU memory.

Only the handoff from Zivid to CuPy is zero-copy. CuPy operations afterwards (e.g. `arr * 1.2`, `.astype(...)`) allocate
new GPU buffers as usual, and `cp.asnumpy(...)` at the end copies to CPU for display. In a real pipeline you would keep
results on the GPU and pass them straight to the next consumer (PyTorch, OpenGL, a CUDA kernel, etc.) -- see the related
samples `capture_and_segment_image_with_pytorch_on_cuda.py` and `capture_and_render_point_cloud_with_opengl_on_cuda.py`.

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
    # The DeviceArray is synchronized into cuda_stream at acquisition, so the
    # device pointer below is a plain accessor that needs no further synchronization.
    device_array = frame_2d.image_device_array(cuda_stream, zivid.PixelFormat.RGBAF)

    print("Getting device pointer")
    device_ptr = device_array.device_pointer()
    height = device_array.shape[0]
    width = device_array.shape[1]
    row_stride_bytes = device_array.strides_in_bytes[0]
    row_stride_elements = device_array.strides[0]
    total_size_bytes = device_array.size_bytes

    print(f"Device pointer: {hex(device_ptr)}")
    print(
        f"Buffer: {width}x{height}, stride={row_stride_bytes} bytes, {row_stride_elements} elements, total size={total_size_bytes} bytes"
    )

    print(
        "Wrapping Zivid's GPU buffer as a CuPy memory pointer (this is the zero-copy step; Zivid still owns the memory)"
    )
    # Note: RGBAf32 format = 4 channels of float32
    unowned_memory = cp.cuda.UnownedMemory(device_ptr, total_size_bytes, owner=device_array)
    unowned_memory_ptr = cp.cuda.MemoryPointer(unowned_memory, 0)

    print("Creating array with correct shape accounting for stride")
    row_elements = row_stride_elements
    # pylint: disable-next=unexpected-keyword-arg
    flat_array = cp.ndarray(shape=(height * row_elements,), dtype=cp.float32, memptr=unowned_memory_ptr)

    print("Reshaping array to image size (height, width, 4 channels)")
    # If stride equals width*16, direct reshape is possible
    if row_stride_bytes == width * 16:
        image_array = flat_array.reshape((height, width, 4))
    else:
        # Handling stride memory by slicing
        image_array = flat_array.reshape((height, row_elements))[:, : width * 4].reshape((height, width, 4))

    print(f"CuPy array shape: {image_array.shape}")
    print(f"CuPy array dtype: {image_array.dtype}")

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
