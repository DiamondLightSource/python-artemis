from time import sleep
from ophyd.sim import motor1, motor2
from bluesky.plan_stubs import mv

def setup_before_gridscan(grid_scan_parameters):
    print("setup_before_gridscan")
    yield from mv(motor1, 2)
    yield from mv(motor2, 2)


def cleanup_after_gridscan():
    print("cleanup_after_gridscan")
    yield from mv(motor1, 0)
    yield from mv(motor2, 0)
