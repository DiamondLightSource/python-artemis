from ophyd.sim import MockFlyer
from bluesky.plan_stubs import mv
from time import sleep


class FastGridScan(MockFlyer):

    def configure(self, grid_scan_parameters):
        print("Configuring FastGridScan")
        yield from mv(self._mot, 0)
        sleep(0.5)
