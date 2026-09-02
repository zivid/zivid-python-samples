"""
Render a Zivid point cloud interactively by copying it device-to-device into OpenGL buffers with CUDA interop.

The point cloud data never goes through CPU memory: Zivid produces it on the GPU as a DeviceArray, CUDA copies it
directly into the OpenGL VBOs (the interop step), and OpenGL renders from those buffers. The CUDA-OpenGL interop happens
at the `cudaMemcpyAsync` from the Zivid device pointer into the CUDA-registered OpenGL buffer. See the related samples
`capture_and_process_image_with_cupy_on_cuda.py` and `capture_and_segment_image_with_pytorch_on_cuda.py` for other
ways to consume Zivid GPU data without a CPU round-trip.

Controls:
- Left-drag: orbit
- Scroll: zoom
- ESC: exit

Requirements:
- CUDA-capable GPU
- glfw: pip install glfw
- PyOpenGL: pip install PyOpenGL

"""

from __future__ import annotations

import ctypes
import math
import sys
from ctypes import byref, c_int, c_size_t, c_uint, c_void_p

import numpy as np
import numpy.typing as npt
import zivid

try:
    import glfw
except ImportError:
    print("⚠️  Failed to import glfw. It is installed via `pip install glfw`.")
    raise

try:
    from OpenGL.GL import (
        GL_ARRAY_BUFFER,
        GL_COLOR_BUFFER_BIT,
        GL_COMPILE_STATUS,
        GL_DEPTH_BUFFER_BIT,
        GL_DEPTH_TEST,
        GL_DYNAMIC_DRAW,
        GL_FALSE,
        GL_FLOAT,
        GL_FRAGMENT_SHADER,
        GL_LINK_STATUS,
        GL_POINTS,
        GL_PROGRAM_POINT_SIZE,
        GL_TRUE,
        GL_UNSIGNED_BYTE,
        GL_VERTEX_SHADER,
        glAttachShader,
        glBindBuffer,
        glBindVertexArray,
        glBufferData,
        glClear,
        glClearColor,
        glCompileShader,
        glCreateProgram,
        glCreateShader,
        glDeleteBuffers,
        glDeleteProgram,
        glDeleteShader,
        glDeleteVertexArrays,
        glDrawArrays,
        glEnable,
        glEnableVertexAttribArray,
        glGenBuffers,
        glGenVertexArrays,
        glGetProgramInfoLog,
        glGetProgramiv,
        glGetShaderInfoLog,
        glGetShaderiv,
        glGetUniformLocation,
        glLinkProgram,
        glShaderSource,
        glUniformMatrix4fv,
        glUseProgram,
        glVertexAttribPointer,
        glViewport,
    )
except ImportError:
    print("⚠️  Failed to import PyOpenGL. It is installed via `pip install PyOpenGL`.")
    raise


# CUDA Runtime ctypes bindings
_CUDA_SUCCESS = 0
_CUDA_MEMCPY_DEVICE_TO_DEVICE = 3
_CUDA_GRAPHICS_REGISTER_FLAGS_NONE = 0


def _load_cuda_runtime(compute_device: zivid.ComputeDevice) -> _CudaRuntime:
    """Load the CUDA runtime shared library matching the SDK's CUDA version.

    Args:
        compute_device: Zivid ComputeDevice instance.

    Returns:
        _CudaRuntime wrapper around the loaded library.

    """
    library_name = compute_device.cuda_runtime_library_name
    if sys.platform == "win32":
        library = ctypes.WinDLL(library_name)
    else:
        library = ctypes.CDLL(library_name)
    return _CudaRuntime(library)


def _check_cuda(cuda_error: int, cuda_function_name: str) -> None:
    """Check CUDA return code and raise on error.

    Args:
        cuda_error: CUDA error code returned by a runtime API call.
        cuda_function_name: Name of the CUDA function for the error message.

    Raises:
        RuntimeError: If cuda_error is not cudaSuccess.

    """
    if cuda_error != _CUDA_SUCCESS:
        raise RuntimeError(f"CUDA error {cuda_error} in {cuda_function_name}")


class _CudaRuntime:
    """Thin wrapper around the CUDA runtime shared library loaded via ctypes.

    All CUDA-GL interop and memory copy operations go through this class.
    """

    def __init__(self, library: ctypes.CDLL) -> None:
        self._library = library

    def graphics_gl_register_buffer(self, gl_buffer_id: int) -> c_void_p:
        """Register an OpenGL buffer object with CUDA for interop.

        Args:
            gl_buffer_id: OpenGL buffer name (GLuint).

        Returns:
            Opaque CUDA graphics resource handle.

        """
        resource = c_void_p()  # pylint: disable=no-value-for-parameter
        cuda_error = self._library.cudaGraphicsGLRegisterBuffer(
            byref(resource),
            c_uint(gl_buffer_id),
            c_uint(_CUDA_GRAPHICS_REGISTER_FLAGS_NONE),
        )
        _check_cuda(cuda_error, "cudaGraphicsGLRegisterBuffer")
        return resource

    def graphics_map_resources(self, resource: c_void_p, stream: int = 0) -> None:
        """Map a CUDA graphics resource for access from CUDA.

        Args:
            resource: Opaque CUDA graphics resource handle.
            stream: CUDA stream pointer (0 for default stream).

        """
        resource_array = (c_void_p * 1)(resource)
        cuda_error = self._library.cudaGraphicsMapResources(c_int(1), resource_array, c_void_p(stream))
        _check_cuda(cuda_error, "cudaGraphicsMapResources")

    def graphics_unmap_resources(self, resource: c_void_p, stream: int = 0) -> None:
        """Unmap a CUDA graphics resource.

        Args:
            resource: Opaque CUDA graphics resource handle.
            stream: CUDA stream pointer (0 for default stream).

        """
        resource_array = (c_void_p * 1)(resource)
        cuda_error = self._library.cudaGraphicsUnmapResources(c_int(1), resource_array, c_void_p(stream))
        _check_cuda(cuda_error, "cudaGraphicsUnmapResources")

    def graphics_resource_get_mapped_pointer(self, resource: c_void_p) -> tuple[int | None, int]:
        """Get the device pointer for a mapped CUDA graphics resource.

        Args:
            resource: Opaque CUDA graphics resource handle.

        Returns:
            Tuple of (device_pointer, size_in_bytes).

        """
        device_pointer = c_void_p()  # pylint: disable=no-value-for-parameter
        size = c_size_t()  # pylint: disable=no-value-for-parameter
        cuda_error = self._library.cudaGraphicsResourceGetMappedPointer(byref(device_pointer), byref(size), resource)
        _check_cuda(cuda_error, "cudaGraphicsResourceGetMappedPointer")
        return device_pointer.value, size.value

    def memcpy_device_to_device(self, dst: int | None, src: int, size_bytes: int, stream: int = 0) -> None:
        """Copy memory between two GPU device pointers.

        Args:
            dst: Destination device pointer.
            src: Source device pointer.
            size_bytes: Number of bytes to copy.
            stream: CUDA stream pointer (0 for default stream).

        """
        cuda_error = self._library.cudaMemcpyAsync(
            c_void_p(dst),
            c_void_p(src),
            c_size_t(size_bytes),
            c_int(_CUDA_MEMCPY_DEVICE_TO_DEVICE),
            c_void_p(stream),
        )
        _check_cuda(cuda_error, "cudaMemcpyAsync")

    def stream_synchronize(self, stream: int = 0) -> None:
        """Block until all operations on the given CUDA stream have completed.

        Args:
            stream: CUDA stream pointer (0 for default stream).

        """
        cuda_error = self._library.cudaStreamSynchronize(c_void_p(stream))
        _check_cuda(cuda_error, "cudaStreamSynchronize")

    def graphics_unregister_resource(self, resource: c_void_p) -> None:
        """Unregister a CUDA graphics resource.

        Args:
            resource: Opaque CUDA graphics resource handle.

        """
        self._library.cudaGraphicsUnregisterResource(resource)


# OpenGL shader helpers

_VERTEX_SHADER_SOURCE = """
#version 330 core
layout(location = 0) in vec4 position;
layout(location = 1) in vec4 color;

uniform mat4 mvp;

out vec4 frag_color;

void main() {
    gl_Position = mvp * vec4(position.xyz, 1.0);
    frag_color = color;
    gl_PointSize = 2.0;
}
"""

_FRAGMENT_SHADER_SOURCE = """
#version 330 core
in vec4 frag_color;
out vec4 out_color;

void main() {
    out_color = frag_color;
}
"""


def _compile_shader(source: str, shader_type: int) -> int:
    """Compile a GLSL shader from source.

    Args:
        source: GLSL source code string.
        shader_type: GL_VERTEX_SHADER or GL_FRAGMENT_SHADER.

    Returns:
        Compiled shader object.

    Raises:
        RuntimeError: If compilation fails.

    """
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        info_log = glGetShaderInfoLog(shader).decode()
        raise RuntimeError(f"Shader compilation failed:\n{info_log}")
    return shader


def _create_shader_program() -> int:
    """Create, compile, and link the point cloud shader program.

    Returns:
        Linked shader program object.

    Raises:
        RuntimeError: If linking fails.

    """
    vertex_shader = _compile_shader(_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
    fragment_shader = _compile_shader(_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        info_log = glGetProgramInfoLog(program).decode()
        raise RuntimeError(f"Shader link failed:\n{info_log}")
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program


def _perspective_matrix(fov_y_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Create a perspective projection matrix.

    Args:
        fov_y_deg: Vertical field of view in degrees.
        aspect: Width / height aspect ratio.
        near: Near clipping plane distance.
        far: Far clipping plane distance.

    Returns:
        4x4 numpy float32 matrix.

    """
    f = 1.0 / math.tan(math.radians(fov_y_deg) / 2.0)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = f / aspect
    matrix[1, 1] = f
    matrix[2, 2] = (far + near) / (near - far)
    matrix[2, 3] = (2.0 * far * near) / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def _look_at(eye: npt.ArrayLike, center: npt.ArrayLike, up: npt.ArrayLike) -> np.ndarray:
    """Create a view matrix (right-handed, looking along -Z in eye space).

    Args:
        eye: Camera position as 3-element array.
        center: Look-at target as 3-element array.
        up: Up direction as 3-element array.

    Returns:
        4x4 numpy float32 matrix.

    """
    eye = np.asarray(eye, dtype=np.float32)
    center = np.asarray(center, dtype=np.float32)
    up = np.asarray(up, dtype=np.float32)

    f = center - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    matrix = np.eye(4, dtype=np.float32)
    matrix[0, :3] = s
    matrix[1, :3] = u
    matrix[2, :3] = -f
    matrix[0, 3] = -np.dot(s, eye)
    matrix[1, 3] = -np.dot(u, eye)
    matrix[2, 3] = np.dot(f, eye)
    return matrix


class _OrbitCamera:
    """Orbit camera controlled by mouse drag and scroll.

    Orbits around a center point. Yaw rotates horizontally, pitch rotates
    vertically. Scroll changes distance from the center.

    The Zivid coordinate system has Y pointing down and Z pointing into the
    scene, so the initial view looks along +Z with Y-down mapped to screen-up.

    """

    def __init__(self, center: list[float], distance: float) -> None:
        self.center = np.array(center, dtype=np.float32)
        self.distance = distance
        # yaw=180 looks along +Z (into the scene, matching the capture viewpoint)
        self.yaw = 180.0
        self.pitch = 0.0
        self._last_x = 0.0
        self._last_y = 0.0
        self._dragging = False

    def view_matrix(self) -> np.ndarray:
        """Compute the view matrix for the current orbit state.

        Returns:
            4x4 numpy float32 view matrix.

        """
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)

        cos_pitch = math.cos(pitch_rad)
        eye = self.center + self.distance * np.array(
            [cos_pitch * math.sin(yaw_rad), math.sin(pitch_rad), cos_pitch * math.cos(yaw_rad)],
            dtype=np.float32,
        )

        # Zivid Y points down; use (0,-1,0) as up so the image appears right-side-up
        return _look_at(eye, self.center, [0.0, -1.0, 0.0])

    def on_mouse_button(self, _window: object, button: int, action: int, _mods: int) -> None:
        """GLFW mouse button callback.

        Args:
            button: Mouse button identifier.
            action: Press or release action.

        """
        if button == glfw.MOUSE_BUTTON_LEFT:
            self._dragging = action == glfw.PRESS
            if self._dragging:
                self._last_x, self._last_y = glfw.get_cursor_pos(_window)

    def on_cursor_pos(self, _window: object, cursor_x: float, cursor_y: float) -> None:
        """GLFW cursor position callback.

        Args:
            cursor_x: Cursor X position.
            cursor_y: Cursor Y position.

        """
        if self._dragging:
            dx = cursor_x - self._last_x
            dy = cursor_y - self._last_y
            self.yaw += dx * 0.3
            self.pitch = max(-89.0, min(89.0, self.pitch - dy * 0.3))
            self._last_x = cursor_x
            self._last_y = cursor_y

    def on_scroll(self, _window: object, _xoffset: float, yoffset: float) -> None:
        """GLFW scroll callback.

        Args:
            yoffset: Vertical scroll offset.

        """
        self.distance = max(10.0, self.distance * (1.0 - yoffset * 0.1))


def _copy_device_array_to_vbo(
    cuda_runtime: _CudaRuntime,
    device_array: zivid.DeviceArray,
    cuda_resource: c_void_p,
) -> None:
    """Copy a DeviceArray into a CUDA-registered OpenGL VBO (device-to-device).

    Args:
        cuda_runtime: _CudaRuntime instance.
        device_array: Zivid DeviceArray already synchronized into the caller's stream.
            Uses size_bytes for transfer size.
        cuda_resource: CUDA graphics resource handle for this VBO.

    """
    src_ptr = device_array.device_pointer()
    cuda_runtime.graphics_map_resources(cuda_resource)
    dst_ptr = cuda_runtime.graphics_resource_get_mapped_pointer(cuda_resource)[0]
    cuda_runtime.memcpy_device_to_device(dst_ptr, src_ptr, device_array.size_bytes)
    cuda_runtime.graphics_unmap_resources(cuda_resource)


def _create_glfw_window() -> object:
    """Initialize GLFW and create an OpenGL 3.3 core profile window.

    Returns:
        GLFW window handle.

    Raises:
        RuntimeError: If GLFW initialization or window creation fails.

    """
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)

    window = glfw.create_window(1280, 960, "Zivid GPU Point Cloud", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")
    glfw.make_context_current(window)
    return window


def _capture_unorganized_point_cloud(app: zivid.Application) -> zivid.UnorganizedPointCloud:
    """Capture a 3D frame and return the unorganized point cloud.

    Args:
        app: Zivid Application instance.

    Returns:
        UnorganizedPointCloud with valid points.

    Raises:
        RuntimeError: If the point cloud has no valid points.

    """
    print("Connecting to camera")
    camera = app.connect_camera()
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing 3D frame")
    frame = camera.capture_2d_3d(settings)
    unorganized_point_cloud = frame.point_cloud().to_unorganized_point_cloud()
    print(f"Unorganized point cloud: {unorganized_point_cloud.size} valid points")

    if unorganized_point_cloud.size == 0:
        raise RuntimeError("Point cloud has no valid points")

    return unorganized_point_cloud


def _create_vao_and_vbos(
    num_points: int, xyzw_array: zivid.DeviceArray, rgba_array: zivid.DeviceArray
) -> tuple[int, int, int, int]:
    """Create the GPU vertex buffers (VBOs) and bind them to the shader via a VAO.

    VBO (Vertex Buffer Object): a chunk of GPU memory holding raw per-vertex data.
    This sample uses two VBOs: one for XYZW positions, one for RGBA colors.

    VAO (Vertex Array Object): an OpenGL object that stores how to interpret one
    or more VBOs -- which buffer feeds which shader input, the data type, the
    stride. Binding the VAO once per draw call restores all that wiring, so the
    render loop only needs to bind the VAO and draw.

    Args:
        num_points: Number of points in the cloud.
        xyzw_array: DeviceArray for XYZW position data.
        rgba_array: DeviceArray for RGBA color data.

    Returns:
        Tuple of (shader_program, vao, position_vbo, color_vbo).

    """
    program = _create_shader_program()

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    # Position VBO: XYZW = 4 floats = 16 bytes per point
    position_vbo = int(glGenBuffers(1))
    glBindBuffer(GL_ARRAY_BUFFER, position_vbo)
    glBufferData(GL_ARRAY_BUFFER, num_points * xyzw_array.strides_in_bytes[0], None, GL_DYNAMIC_DRAW)
    # Attribute 0: position (matches layout(location = 0) in vertex shader)
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)

    # Color VBO: RGBA = 4 uint8 = 4 bytes per point (normalized to [0,1] by GL)
    color_vbo = int(glGenBuffers(1))
    glBindBuffer(GL_ARRAY_BUFFER, color_vbo)
    glBufferData(GL_ARRAY_BUFFER, num_points * rgba_array.strides_in_bytes[0], None, GL_DYNAMIC_DRAW)
    # Attribute 1: color (matches layout(location = 1) in vertex shader)
    glVertexAttribPointer(1, 4, GL_UNSIGNED_BYTE, GL_TRUE, 0, None)
    glEnableVertexAttribArray(1)

    glBindVertexArray(0)
    return program, vao, position_vbo, color_vbo


def _render_loop(window: object, orbit: _OrbitCamera, mvp_uniform_location: int, vao: int, num_points: int) -> None:
    """Run the interactive render loop until the window is closed or ESC is pressed.

    Args:
        window: GLFW window handle.
        orbit: Orbit camera for view matrix computation.
        mvp_uniform_location: Uniform location for the MVP matrix in the shader.
        vao: OpenGL vertex array object.
        num_points: Number of points to draw.

    """
    while not glfw.window_should_close(window):
        glfw.poll_events()
        if glfw.get_key(window, glfw.KEY_ESCAPE) == glfw.PRESS:
            break

        framebuffer_width, framebuffer_height = glfw.get_framebuffer_size(window)
        if framebuffer_width == 0 or framebuffer_height == 0:
            continue

        glViewport(0, 0, framebuffer_width, framebuffer_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        projection = _perspective_matrix(60.0, framebuffer_width / framebuffer_height, 1.0, 100000.0)
        view = orbit.view_matrix()
        mvp = projection @ view

        glUniformMatrix4fv(mvp_uniform_location, 1, GL_TRUE, mvp)
        glBindVertexArray(vao)
        glDrawArrays(GL_POINTS, 0, num_points)
        glBindVertexArray(0)

        glfw.swap_buffers(window)


def _main() -> None:
    window = _create_glfw_window()

    print("Initializing Zivid application")
    app = zivid.Application()

    print("Verifying that CUDA backend is available")
    compute_device = app.compute_device()
    if compute_device.backend != zivid.ComputeBackend.cuda:
        raise RuntimeError("This sample requires CUDA backend")
    print(f"Using GPU: {compute_device.model}")

    print("Loading the CUDA runtime library that the Zivid SDK was built against")
    cuda_runtime = _load_cuda_runtime(compute_device)

    unorganized_point_cloud = _capture_unorganized_point_cloud(app)
    num_points = unorganized_point_cloud.size

    print("Getting GPU device arrays for points and colors (data stays on GPU)")
    # The device arrays are synchronized into cuda_stream at acquisition, so the
    # device pointers used during the copy below are plain accessors.
    cuda_stream = zivid.CUDAStreamPtr()  # default stream
    xyzw_array = unorganized_point_cloud.device_points_xyzw(cuda_stream)
    rgba_array = unorganized_point_cloud.device_colors(cuda_stream, zivid.PixelFormat.RGBA)
    print(f"Position (XYZW): {xyzw_array.shape[0]} points, {xyzw_array.strides_in_bytes[0]} bytes/point")
    print(f"Color (RGBA): {rgba_array.shape[0]} points, {rgba_array.strides_in_bytes[0]} bytes/point")

    print("Creating OpenGL vertex array and buffers")
    program, vao, position_vbo, color_vbo = _create_vao_and_vbos(num_points, xyzw_array, rgba_array)
    mvp_uniform_location = glGetUniformLocation(program, "mvp")

    print("Registering OpenGL buffers with CUDA (so CUDA can write into them)")
    position_cuda_resource = cuda_runtime.graphics_gl_register_buffer(position_vbo)
    color_cuda_resource = cuda_runtime.graphics_gl_register_buffer(color_vbo)

    print(
        "Copying point cloud GPU -> GPU into OpenGL buffers (this is the CUDA-OpenGL interop step; no CPU round-trip)"
    )
    _copy_device_array_to_vbo(cuda_runtime, xyzw_array, position_cuda_resource)
    _copy_device_array_to_vbo(cuda_runtime, rgba_array, color_cuda_resource)

    print("Synchronizing CUDA stream to ensure transfer is complete")
    cuda_runtime.stream_synchronize()
    print("Transfer complete")

    print("Setting up orbit camera")
    centroid = unorganized_point_cloud.centroid()
    if centroid is not None:
        center = centroid.tolist()
    else:
        center = [0.0, 0.0, 1000.0]

    # Initial distance: back away from the centroid along the Z axis
    distance = max(abs(center[2]) * 0.8, 500.0)
    orbit = _OrbitCamera(center, distance)

    glfw.set_mouse_button_callback(window, orbit.on_mouse_button)
    glfw.set_cursor_pos_callback(window, orbit.on_cursor_pos)
    glfw.set_scroll_callback(window, orbit.on_scroll)

    print("Configuring OpenGL state")
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_PROGRAM_POINT_SIZE)
    glClearColor(0.05, 0.05, 0.05, 1.0)
    glUseProgram(program)

    print("Rendering. Left-drag to orbit, scroll to zoom, ESC to exit.")
    _render_loop(window, orbit, mvp_uniform_location, vao, num_points)

    # Cleanup
    cuda_runtime.graphics_unregister_resource(position_cuda_resource)
    cuda_runtime.graphics_unregister_resource(color_cuda_resource)
    glDeleteBuffers(2, [position_vbo, color_vbo])
    glDeleteVertexArrays(1, [vao])
    glDeleteProgram(program)
    glfw.terminate()
    print("Done")


if __name__ == "__main__":
    _main()
