import pytest

from testbench2robotframework.utils import replace_invalid_characters

invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']


@pytest.mark.parametrize("invalid_char", invalid_chars)
def test_filename_does_not_contain_invalid_char(invalid_char):
    filename = f"1.2.1 Testsuite with {invalid_char} in the name.robot"
    assert replace_invalid_characters(filename).find(invalid_char) == -1
