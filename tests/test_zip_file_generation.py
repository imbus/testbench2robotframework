import os
import shutil
from pathlib import Path

import pytest
from robot.parsing.model.blocks import File

from testbench2robotframework.testsuite_write import (
    clear_generation_directory,
    directory_to_zip,
    write_test_suite_files,
)


def test_previous_zip_gets_deleted():
    generation_dir = Path("./tests/test_data/Generated")
    if not os.path.isdir("./tests/test_data/Generated"):
        os.mkdir("./tests/test_data/Generated")
    shutil.make_archive(str(generation_dir), 'zip', str(generation_dir))
    clear_generation_directory(generation_dir)
    assert not os.path.exists(generation_dir)


def test_zip_gets_created():
    test_suites = {"iTB-TC-322-PC-12121212212": File()}
    generation_dir = Path("./tests/test_data/Generated/zip_file")
    write_test_suite_files(test_suites, generation_dir)
    directory_to_zip(generation_dir)
    assert os.path.exists("".join([str(generation_dir), ".zip"]))
