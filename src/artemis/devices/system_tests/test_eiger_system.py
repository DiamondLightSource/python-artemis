import numpy as np
import pytest
from src.artemis.devices.eiger import DetectorParams, EigerDetector


@pytest.fixture()
def eiger():
    detector_params: DetectorParams = DetectorParams(
        current_energy=100,
        exposure_time=0.1,
        acquisition_id="test",
        directory="/tmp",
        prefix="file_name",
        detector_distance=100.0,
        omega_start=0.0,
        omega_increment=0.1,
        num_images=50,
        use_roi_mode=False,
    )
    eiger = EigerDetector(
        detector_params=detector_params, name="eiger", prefix="BL03S-EA-EIGER-01:"
    )

    # Otherwise odin moves too fast to be tested
    eiger.cam.manual_trigger.put("Yes")

    # S03 currently does not have StaleParameters_RBV
    eiger.wait_for_stale_parameters = lambda: None

    yield eiger


@pytest.mark.s03
def test_can_stage_and_unstage_eiger(eiger: EigerDetector):
    times_id_has_changed = 0

    def file_writer_id_monitor(*_, **kwargs):
        nonlocal times_id_has_changed
        if not np.array_equal(kwargs["old_value"], kwargs["value"]):
            times_id_has_changed += 1

    eiger.odin.file_writer.id.subscribe(file_writer_id_monitor)
    eiger.stage()
    assert (
        times_id_has_changed == 2
    )  # Once for initial connection and once for changing the value
    assert eiger.cam.acquire.get() == 1
    # S03 filewriters stay in error
    eiger.odin.check_odin_initialised = lambda: (True, "")
    eiger.unstage()
    assert eiger.cam.acquire.get() == 0
