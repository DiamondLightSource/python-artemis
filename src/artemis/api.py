from src.artemis.plans.beamline_setup import (
    setup_before_gridscan,
    cleanup_after_gridscan,
)
from src.artemis.plans.ispyb import (
    register_collection,
    update_status,
)
from src.artemis.plans.nexus import (
    create_nexus_file,
    write_endtime,
)
from src.artemis.plans.analysis import trigger_analysis
from src.artemis.plans.gridscan import gridscan
from src.artemis.plans.results import get_results


def run_gridscan(gridscan_parameters):
    try:
        yield from setup_before_gridscan(gridscan_parameters)
        register_collection(gridscan_parameters)
        create_nexus_file(gridscan_parameters)
        trigger_analysis()
        yield from gridscan(gridscan_parameters)
        update_status()
        write_endtime()
        get_results()
    finally:
        yield from cleanup_after_gridscan()
