from artemis.devices.eiger import Eiger
from artemis.devices.zebra import Zebra
from artemis.devices.fast_grid_scan import FastGridScan
from bluesky.preprocessors import stage_decorator
from ophyd.sim import motor, motor1, motor2, det


def gridscan(grid_scan_parameters):
    # Setup devices using base PVs from grid_scan_parameters:
    eiger = Eiger('eiger', motor1, 'motor1', center=0, Imax=1, sigma=1)
    zebra = Zebra('zebra', motor2, 'motor2', center=0, Imax=1, sigma=1)
    fast_grid_scan = FastGridScan('fastgridscanlfyer', det, motor, 1, 5, 20)

    @stage_decorator([eiger, zebra])
    def run():
        print("triggering gridscan")
        yield from fast_grid_scan.configure(grid_scan_parameters)
        fast_grid_scan.kickoff()
        fast_grid_scan.complete()

    yield from run()
