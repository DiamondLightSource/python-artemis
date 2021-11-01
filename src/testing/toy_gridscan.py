from bluesky import RunEngine
from src.artemis.api import run_gridscan

def run_toy_gridscan():
    RE = RunEngine()
    RE(run_gridscan({}))
