"""
Poll the camera health check from a separate thread while capturing in the main thread, printing the statuses and values every second.

"""

import threading
import time

import zivid


def _print_healthcheck(health: zivid.CameraHealth) -> None:
    temperature = health.temperature
    print(f"Overall:                {health.overall}")
    print(f"  Max transfer speed:   {health.max_transfer_speed.status} ({health.max_transfer_speed.value} Mbps)")
    print(f"  Temperature (DMD):    {temperature.dmd.status} ({temperature.dmd.value} C)")
    print(f"  Temperature (LED):    {temperature.led.status} ({temperature.led.value} C)")
    print(f"  Temperature (Lens):   {temperature.lens.status} ({temperature.lens.value} C)")
    print(f"  Fan:                  {health.fan.status} ({health.fan.value})")
    print(f"  Memory:               {health.memory.status} ({health.memory.value} errors)")
    print(f"  Infield verification: {health.infield_verification.status} ({health.infield_verification.value})")


def _main() -> None:
    app = zivid.Application()

    print("Connecting to camera")
    camera = app.connect_camera()

    poll_interval = 1
    stop = threading.Event()

    def poll() -> None:
        while not stop.is_set():
            _print_healthcheck(camera.check_health())
            print()
            stop.wait(poll_interval)

    polling_thread = threading.Thread(target=poll)
    polling_thread.start()

    settings = zivid.Settings(acquisitions=[zivid.Settings.Acquisition()])
    capture_cycle = 5
    number_of_captures = 5

    for i in range(1, number_of_captures + 1):
        camera.capture_3d(settings)
        print(f"Captured frame {i} of {number_of_captures}")
        if i < number_of_captures:
            time.sleep(capture_cycle)

    stop.set()
    polling_thread.join()


if __name__ == "__main__":
    _main()
