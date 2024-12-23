from invoke import Context, task
import os
from pathlib import Path
from robot.run import run_cli

@task
def run_atest(c: Context) -> None:
    """Runs Robot Framework atests."""
    exedir = Path.cwd() / "atest"
    orgdir = Path.cwd()
    os.chdir(exedir)
    try:
        run_cli(
            [
                "-d",
                "./results",
                "-L",
                "TRACE",
                "-P",
                "robot/libs",
                "-P",
                "robot/resources",
                "-v",
                f"ATEST_DIR:{exedir}",
                "robot",
            ]
        )
    finally:
        os.chdir(orgdir)