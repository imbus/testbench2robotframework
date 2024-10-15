from invoke import Context, task  # type: ignore
from robot.run import run_cli  # type: ignore
from pathlib import Path
import os

@task
def roundtrip(
    c: Context,
) -> None:
    exedir = Path.cwd() / "new_json"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        c.run("testbench-cli-reporter -c ./cli_reporter_LargeDataSet.json")
        c.run("testbench2robotframework write -c ./config.json ./big_data.zip")
        args = []
        run_cli(
            [
                "-d",
                "./results",
                "-P",
                str((exedir / "libs").resolve()),
                "-P",
                str((exedir / "resources").resolve()),
                "--xunit",
                "junit.xml",
                "--nostatusrc",
                "--loglevel",
                "TRACE:INFO",
                *args,
                "--variablefile",
                "./localization/en.json",
                "./Generated/",
            ]
        )
        c.run("testbench2robotframework read -c ./config.json -o ./results/output.xml ./big_data.zip")
    finally:
        os.chdir(orgdir)


@task
def generate_robot(
    c: Context,
) -> None:
    exedir = Path.cwd() / "new_json"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        c.run("testbench2robotframework write -c ./config.json ./big_data.zip")
    finally:
        os.chdir(orgdir)

@task
def export_json(
    c: Context,
) -> None:
    exedir = Path.cwd() / "new_json"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        c.run("testbench-cli-reporter -c ./cli_reporter_LargeDataSet.json")
    finally:
        os.chdir(orgdir)

@task
def run_robot(
    c: Context,
) -> None:
    exedir = Path.cwd() / "new_json"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        args = []
        run_cli(
            [
                "-d",
                "./results",
                "-P",
                str((exedir / "libs").resolve()),
                "-P",
                str((exedir / "resources").resolve()),
                "--xunit",
                "junit.xml",
                "--nostatusrc",
                "--loglevel",
                "TRACE:INFO",
                *args,
                "--variablefile",
                "./localization/en.json",
                "./Generated/",
            ]
        )
    finally:
        os.chdir(orgdir)

@task
def read_results(
    c: Context,
) -> None:
    exedir = Path.cwd() / "new_json"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        c.run("testbench2robotframework read -c ./config.json -o ./results/output.xml ./big_data.zip")
    finally:
        os.chdir(orgdir)