import os
from collections import namedtuple
from pathlib import Path
from unittest.mock import call, patch

import h5py
import pytest

from src.artemis.nexus_writing.write_nexus import NexusWriter
from src.artemis.parameters import FullParameters

"""It's hard to effectively unit test the nexus writing so these are really system tests 
that confirms that we're passing the right sorts of data to nexgen to get a sensible output.
Note that the testing process does now write temporary files to disk."""

ParamsAndNexusWriter = namedtuple("ParamsAndNexusWriter", ["params", "nexus_writer"])


def get_minimum_parameters_for_file_writing() -> FullParameters:
    test_full_params = FullParameters()
    test_full_params.ispyb_params.wavelength = 1.0
    test_full_params.ispyb_params.flux = 9.0
    test_full_params.ispyb_params.transmission = 0.5
    return test_full_params


def assert_start_data_correct(params_and_nexus_writer: ParamsAndNexusWriter):
    test_full_params, nexus_writer = params_and_nexus_writer
    for filename in [nexus_writer.nexus_file, nexus_writer.master_file]:
        with h5py.File(filename, "r") as written_nexus_file:
            sam_x_data = written_nexus_file["/entry/data/sam_x"][:]
            assert len(sam_x_data) == (
                test_full_params.grid_scan_params.x_steps + 1
            ) * (test_full_params.grid_scan_params.y_steps + 1)
            assert sam_x_data[1] - sam_x_data[0] == pytest.approx(
                test_full_params.grid_scan_params.x_step_size
            )
            assert written_nexus_file["/entry/instrument/beam/total_flux"][()] == 9.0


def assert_end_data_correct(nexus_writer: NexusWriter):
    for filename in [nexus_writer.nexus_file, nexus_writer.master_file]:
        with h5py.File(filename, "r") as written_nexus_file:
            assert "end_time" in written_nexus_file["entry"]


@pytest.fixture
def params_and_nexus_writer():
    test_full_params = get_minimum_parameters_for_file_writing()
    nexus_writer = NexusWriter(test_full_params)
    yield ParamsAndNexusWriter(test_full_params, nexus_writer)
    # cleanup: delete test nexus file
    for filename in [nexus_writer.nexus_file, nexus_writer.master_file]:
        file_path = filename.parent / f"{filename.name}"
        os.remove(file_path)


def test_given_full_params_when_enter_called_then_files_written_as_expected(
    params_and_nexus_writer,
):
    params_and_nexus_writer.nexus_writer.__enter__()

    assert_start_data_correct(params_and_nexus_writer)


def test_given_full_params_and_nexus_file_with_entry_when_exit_called_then_end_time_written_to_file(
    params_and_nexus_writer,
):
    nexus_writer = params_and_nexus_writer.nexus_writer
    nexus_writer.__enter__()

    for file in [nexus_writer.nexus_file, nexus_writer.master_file]:
        with h5py.File(file, "r+") as written_nexus_file:
            written_nexus_file.require_group("entry")

    nexus_writer.__exit__()

    assert_end_data_correct(nexus_writer)


def test_given_parameters_when_nexus_writer_used_as_context_manager_then_all_data_in_file(
    params_and_nexus_writer,
):
    nexus_writer = params_and_nexus_writer.nexus_writer
    with nexus_writer:
        pass

    assert_start_data_correct(params_and_nexus_writer)
    assert_end_data_correct(nexus_writer)


@pytest.mark.parametrize(
    "num_images, expected_num_of_files",
    [(2540, 3), (4000, 4), (8999, 9)],
)
def test_given_number_of_images_above_1000_then_expected_datafiles_used(
    num_images, expected_num_of_files
):
    params = FullParameters()
    params.detector_params.num_images = num_images
    nexus_writer = NexusWriter(params)
    assert len(nexus_writer.get_image_datafiles()) == expected_num_of_files
    paths = [str(filename) for filename in nexus_writer.get_image_datafiles()]
    expected_paths = [
        f"/tmp/file_name_0_00000{i + 1}.h5" for i in range(expected_num_of_files)
    ]
    assert paths == expected_paths


@pytest.fixture
def dummy_nexus_writer():
    params = FullParameters()
    params.detector_params.use_roi_mode = True
    params.detector_params.num_images = 1044
    params.detector_params.directory = (
        os.path.dirname(os.path.realpath(__file__)) + "/test_data"
    )
    params.detector_params.prefix = "dummy"
    nexus_writer = NexusWriter(params)

    yield nexus_writer

    os.remove(nexus_writer.nexus_file)
    os.remove(nexus_writer.master_file)


def test_given_dummy_data_then_datafile_written_correctly(dummy_nexus_writer):
    dummy_nexus_writer.__enter__()

    with h5py.File(dummy_nexus_writer.nexus_file) as f:
        assert f["entry"]["data"]["data"][1043, 0, 0] == 0

        with pytest.raises(IndexError):
            assert f["entry"]["data"]["data"][1044, 0, 0] == 0


def test_nexus_writer_files_are_formatted_as_expected():
    parameters = get_minimum_parameters_for_file_writing()
    nexus_writer = NexusWriter(parameters)

    for file in [nexus_writer.nexus_file, nexus_writer.master_file]:
        file_name = os.path.basename(file.name)
        expected_file_name_prefix = parameters.detector_params.prefix + "_0"
        assert file_name.startswith(expected_file_name_prefix)


def test_nexus_writer_opens_temp_file_on_exit(params_and_nexus_writer):
    nexus_writer = params_and_nexus_writer.nexus_writer
    nexus_file = nexus_writer.nexus_file
    master_file = nexus_writer.master_file
    temp_nexus_file = Path(f"{str(nexus_file)}.tmp")
    temp_master_file = Path(f"{str(master_file)}.tmp")
    calls_with_temp = [call(temp_nexus_file, "r+"), call(temp_master_file, "r+")]
    calls_without_temp = [call(nexus_file, "r+"), call(master_file, "r+")]

    nexus_writer.__enter__()

    with patch("h5py.File") as mock_h5py_file:
        nexus_writer.__exit__()
        actual_mock_calls = mock_h5py_file.mock_calls
        assert all(call in actual_mock_calls for call in calls_with_temp)
        assert all(call not in actual_mock_calls for call in calls_without_temp)
