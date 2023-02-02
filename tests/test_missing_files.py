import pytest

from testbench2robotframework.utils import get_directory


def test_json_dir_does_not_exist():
    json_files_path = "invalid/file/path"
    with pytest.raises(SystemExit):
        get_directory(json_files_path)
