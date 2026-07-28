"""
Demonstrate zero-copy GPU interop by handing a Zivid DeviceArray to PyTorch on the GPU, showing two paths.

DISCLAIMER: Zivid does not provide or support the third-party library used in this sample. PyTorch is an external
dependency that the user is responsible for installing, configuring, and maintaining. This sample exists solely to
demonstrate how to expose Zivid GPU data to a GPU framework without a CPU round-trip.

There are two ways to get a Zivid DeviceArray into PyTorch on the GPU:

1. Primary, recommended path -- the CUDA Array Interface. zivid-python already implements ``__cuda_array_interface__``
   on DeviceArray (CUDA backend only), so ``torch.as_tensor(device_array, device="cuda")`` imports the Zivid GPU
   buffer into PyTorch zero-copy, with no manual pointer, shape, or stride handling and no ctypes or PyCapsule code.
   This is the simple path.

2. Optional path -- build a DLPack capsule yourself. Only needed when you must produce a DLPack capsule directly from
   the DeviceArray, for a consumer that expects the ``__dlpack__`` protocol directly (for example from C++). This
   path constructs a ``DLManagedTensor`` from the raw building blocks the DeviceArray exposes (device
   pointer, shape, strides in elements, element data type, CUDA device) using ctypes, wraps it in the standard
   ``__dlpack__`` / ``__dlpack_device__`` protocol, and hands it to ``torch.from_dlpack``. The DeviceArray is kept
   alive by the tensor's manager context and released only when the consumer is done with it.

Only the hand-off is zero-copy in both paths: PyTorch views Zivid's GPU memory directly (verified below by comparing
data pointers). Any subsequent PyTorch operation allocates new GPU buffers as usual. See the related samples
``capture_and_process_image_with_cupy_on_cuda.py``, ``capture_and_segment_image_with_pytorch_on_cuda.py``, and
``capture_and_render_point_cloud_with_opengl_on_cuda.py`` for other ways to consume Zivid GPU data without a CPU
round-trip.

Requirements:
- CUDA-capable GPU
- PyTorch with CUDA support: pip install torch

"""

from __future__ import annotations

import ctypes
from typing import Optional, Tuple

import zivid

try:
    import torch
except ImportError:
    print("⚠️  Failed to import PyTorch. It is installed via `pip install torch`.")
    raise


_KDLCUDA = 2
_KDLINT = 0
_KDLUINT = 1
_KDLFLOAT = 2

_DLTENSOR_CAPSULE_NAME = b"dltensor"


class _DLDevice(ctypes.Structure):  # pylint: disable=too-few-public-methods
    _fields_ = [("device_type", ctypes.c_int), ("device_id", ctypes.c_int32)]


class _DLDataType(ctypes.Structure):  # pylint: disable=too-few-public-methods
    _fields_ = [("code", ctypes.c_uint8), ("bits", ctypes.c_uint8), ("lanes", ctypes.c_uint16)]


class _DLTensor(ctypes.Structure):  # pylint: disable=too-few-public-methods
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("device", _DLDevice),
        ("ndim", ctypes.c_int32),
        ("dtype", _DLDataType),
        ("shape", ctypes.POINTER(ctypes.c_int64)),
        ("strides", ctypes.POINTER(ctypes.c_int64)),
        ("byte_offset", ctypes.c_uint64),
    ]


class _DLManagedTensor(ctypes.Structure):  # pylint: disable=too-few-public-methods
    pass


_DLManagedTensorDeleter = ctypes.CFUNCTYPE(None, ctypes.POINTER(_DLManagedTensor))

_DLManagedTensor._fields_ = [  # pylint: disable=protected-access
    ("dl_tensor", _DLTensor),
    ("manager_ctx", ctypes.c_void_p),
    ("deleter", _DLManagedTensorDeleter),
]


_pythonapi = ctypes.pythonapi
_PyCapsule_New = _pythonapi.PyCapsule_New
_PyCapsule_New.restype = ctypes.py_object
_PyCapsule_New.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]


_MANAGER_CONTEXTS: dict = {}


@_DLManagedTensorDeleter
def _release_managed_tensor(managed_pointer: "ctypes._Pointer[_DLManagedTensor]") -> None:
    address = ctypes.addressof(managed_pointer.contents)
    _MANAGER_CONTEXTS.pop(address, None)


def _dl_data_type(device_array: zivid.DeviceArray) -> _DLDataType:
    typestr = device_array.__cuda_array_interface__["typestr"]
    kind = typestr[1]
    bits = int(typestr[2:]) * 8
    code = {"f": _KDLFLOAT, "u": _KDLUINT, "i": _KDLINT}[kind]
    return _DLDataType(code=code, bits=bits, lanes=1)  # pylint: disable=no-value-for-parameter


def _build_dl_managed_tensor(device_array: zivid.DeviceArray, device_id: int) -> ctypes.c_void_p:
    """Build a DLManagedTensor that references the DeviceArray's GPU buffer.

    Args:
        device_array: The Zivid DeviceArray whose device memory is exposed.
        device_id: The CUDA device ordinal the buffer lives on.

    Returns:
        The address of the DLManagedTensor as a ctypes void pointer.

    """
    shape = tuple(int(dimension) for dimension in device_array.shape)
    strides = tuple(int(stride) for stride in device_array.strides)

    shape_array = (ctypes.c_int64 * len(shape))(*shape)
    strides_array = (ctypes.c_int64 * len(strides))(*strides)

    managed = _DLManagedTensor()
    managed.dl_tensor.data = ctypes.c_void_p(device_array.device_pointer())
    managed.dl_tensor.device = _DLDevice(_KDLCUDA, device_id)  # pylint: disable=no-value-for-parameter
    managed.dl_tensor.ndim = len(shape)
    managed.dl_tensor.dtype = _dl_data_type(device_array)
    managed.dl_tensor.shape = shape_array
    managed.dl_tensor.strides = strides_array
    managed.dl_tensor.byte_offset = 0
    managed.deleter = _release_managed_tensor  # pylint: disable=attribute-defined-outside-init

    _MANAGER_CONTEXTS[ctypes.addressof(managed)] = (managed, shape_array, strides_array, device_array)
    return ctypes.cast(ctypes.byref(managed), ctypes.c_void_p)


class ZividDeviceArrayDLPack:  # pylint: disable=too-few-public-methods
    """Expose a Zivid DeviceArray to DLPack consumers via the ``__dlpack__`` / ``__dlpack_device__`` protocol.

    The DeviceArray is kept alive until the consumer releases the imported tensor.
    """

    def __init__(self, device_array: zivid.DeviceArray, device_id: int) -> None:
        """Wrap a DeviceArray for DLPack consumption.

        Args:
            device_array: The Zivid DeviceArray to expose. Must be on the CUDA backend.
            device_id: The CUDA device ordinal the buffer lives on.

        Raises:
            RuntimeError: If the DeviceArray is not on the CUDA backend.

        """
        if device_array.backend != zivid.ComputeBackend.cuda:
            raise RuntimeError("DLPack construction in this sample is scoped to the CUDA backend")
        self._device_array = device_array
        self._device_id = device_id

    def __dlpack_device__(self) -> Tuple[int, int]:
        """Return the DLPack device tuple for the buffer.

        Returns:
            A ``(device_type, device_id)`` tuple with ``device_type`` set to kDLCUDA.

        """
        return (_KDLCUDA, self._device_id)

    def __dlpack__(self, stream: Optional[int] = None, **kwargs: object) -> object:  # pylint: disable=unused-argument
        """Return a PyCapsule named "dltensor" wrapping a DLManagedTensor for the DeviceArray's GPU buffer.

        Args:
            stream: The consumer's CUDA stream, accepted for protocol compatibility. The DeviceArray was already
                synchronized against the stream it was acquired on, so no extra synchronization is done here.
            kwargs: Additional protocol keyword arguments (e.g. ``max_version``), accepted and ignored.

        Returns:
            A PyCapsule named ``"dltensor"`` wrapping a DLManagedTensor.

        """
        managed = _build_dl_managed_tensor(self._device_array, self._device_id)
        return _PyCapsule_New(managed, _DLTENSOR_CAPSULE_NAME, None)


def _main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("This sample requires PyTorch with CUDA support")

    torch_device = torch.device("cuda")
    print(f"PyTorch CUDA device: {torch.cuda.get_device_name()}")
    torch.zeros(1, device=torch_device)

    print("Initializing Zivid application (will reuse PyTorch's CUDA context)")
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

    print("Creating a PyTorch CUDA stream for GPU operations")
    pytorch_stream = torch.cuda.Stream()
    print(f"Using CUDA stream: {hex(pytorch_stream.cuda_stream)}")

    print("Getting GPU device buffer in float format (RGBAf32), synchronized into the PyTorch stream")
    zivid_stream = zivid.CUDAStreamPtr(pytorch_stream.cuda_stream)
    device_array = frame_2d.image_device_array(zivid_stream, zivid.PixelFormat.RGBAF)
    print(f"DeviceArray: shape={tuple(device_array.shape)}, strides(elements)={tuple(device_array.strides)}")
    print(f"DeviceArray device pointer: {hex(device_array.device_pointer())}")

    with torch.cuda.stream(pytorch_stream):
        print("Primary path: CUDA Array Interface (no ctypes, no PyCapsule)")
        torch_image = torch.as_tensor(device_array, device="cuda")  # zero-copy via __cuda_array_interface__
        print(
            f"PyTorch tensor: shape={tuple(torch_image.shape)}, dtype={torch_image.dtype}, device={torch_image.device}"
        )
        if torch_image.data_ptr() != device_array.device_pointer():
            raise RuntimeError("Zero-copy check failed: PyTorch tensor does not share the Zivid device pointer")
        print("Zero-copy verified: PyTorch tensor shares the Zivid device pointer")

        print("Optional path: build a DLPack capsule directly from the DeviceArray and import it")
        dlpack_source = ZividDeviceArrayDLPack(device_array, torch.cuda.current_device())
        torch_image_via_capsule = torch.from_dlpack(dlpack_source)
        if torch_image_via_capsule.data_ptr() != device_array.device_pointer():
            raise RuntimeError("Zero-copy check failed: capsule tensor does not share the Zivid device pointer")
        print("Zero-copy verified: DLPack-capsule tensor shares the Zivid device pointer")

        print("Example: computing mean color on the GPU from the imported tensor")
        mean_rgba = torch_image.float().mean(dim=(0, 1))

    pytorch_stream.synchronize()
    mean_values = mean_rgba.cpu().tolist()
    print(
        "Mean RGBA values: "
        f"R={mean_values[0]:.3f}, G={mean_values[1]:.3f}, B={mean_values[2]:.3f}, A={mean_values[3]:.3f}"
    )


if __name__ == "__main__":
    _main()
