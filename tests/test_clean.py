"""'clean' removes previously generated suites - and nothing else."""

from pathlib import Path

from testbench2robotframework.testsuite_write import clear_generation_directory, is_generated_suite

GENERATED = (
    "*** Settings ***\n"
    "Metadata    UniqueID    itb-TC-1\n"
    "Metadata    Name    Set\n\n"
    "*** Test Cases ***\nitb-TC-1-PC-1\n    Log    x\n"
)
HAND_WRITTEN = "*** Test Cases ***\nMy Test\n    Log    x\n"


def build_tree(root: Path) -> dict[str, Path]:
    files = {
        "generated_suite": root / "1__Theme" / "1__Set.robot",
        "generated_init": root / "1__Theme" / "__init__.robot",
        "stale_copy": root / "old" / "copy.robot",
        "hand_written": root / "hand_written.robot",
        "note": root / "1__Theme" / "note.txt",
        "resource": root / "resources" / "common.resource",
    }
    for path in files.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    files["generated_suite"].write_text(GENERATED, encoding="utf-8")
    files["generated_init"].write_text(
        "*** Settings ***\nMetadata    UniqueID    itb-TT-1\n", encoding="utf-8"
    )
    files["stale_copy"].write_text(GENERATED, encoding="utf-8")
    files["hand_written"].write_text(HAND_WRITTEN, encoding="utf-8")
    files["note"].write_text("notes", encoding="utf-8")
    files["resource"].write_text("*** Keywords ***\nKw\n    Log    x\n", encoding="utf-8")
    return files


def test_only_generated_robot_files_are_recognised(tmp_path):
    files = build_tree(tmp_path)

    assert is_generated_suite(files["generated_suite"])
    assert is_generated_suite(files["generated_init"])
    assert not is_generated_suite(files["hand_written"])


def test_clean_removes_generated_files_and_keeps_everything_else(tmp_path):
    files = build_tree(tmp_path)

    clear_generation_directory(tmp_path)

    assert not files["generated_suite"].exists()
    assert not files["generated_init"].exists()
    assert not files["stale_copy"].exists()
    assert files["hand_written"].exists()
    assert files["note"].exists()
    assert files["resource"].exists()


def test_directories_left_empty_are_removed_but_the_root_stays(tmp_path):
    files = build_tree(tmp_path)

    clear_generation_directory(tmp_path)

    assert not files["stale_copy"].parent.exists()  # 'old/' only held a generated file
    assert files["note"].parent.exists()  # '1__Theme/' still holds the note
    assert tmp_path.exists()  # the output root itself is never removed


def test_nested_empty_directory_chain_is_removed(tmp_path):
    deep = tmp_path / "a" / "b" / "c" / "suite.robot"
    deep.parent.mkdir(parents=True)
    deep.write_text(GENERATED, encoding="utf-8")

    clear_generation_directory(tmp_path)

    assert not (tmp_path / "a").exists()
    assert tmp_path.exists()


def test_zip_target_is_removed_as_a_whole(tmp_path):
    target = tmp_path / "suites.zip"
    target.write_bytes(b"PK...")

    clear_generation_directory(target)

    assert not target.exists()


def test_missing_directory_is_no_error(tmp_path):
    clear_generation_directory(tmp_path / "does_not_exist")


def test_clean_mode_all_wipes_everything(tmp_path):
    from testbench2robotframework.testsuite_write import wipe_generation_directory

    files = build_tree(tmp_path)

    wipe_generation_directory(tmp_path)

    assert not tmp_path.exists()
    assert not files["hand_written"].exists()


def test_clean_mode_is_config_only_and_defaults_to_generated():
    import click

    from testbench2robotframework.cli import generate_tests
    from testbench2robotframework.config import CleanMode, Configuration

    assert Configuration.from_dict({}).clean_mode is CleanMode.GENERATED
    assert Configuration.from_dict({"clean-mode": "all"}).clean_mode is CleanMode.ALL
    # deliberately no CLI flag for the full wipe
    assert not any("clean-mode" in str(p.opts) for p in generate_tests.params)


def test_clean_flag_is_tristate():
    from testbench2robotframework.cli import generate_tests

    clean = next(p for p in generate_tests.params if "--clean" in p.opts)

    assert clean.default is None  # absent -> the configuration decides
    assert "--no-clean" in clean.secondary_opts
