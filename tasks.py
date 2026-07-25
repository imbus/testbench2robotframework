import os
import re
from pathlib import Path

from invoke import Context, task
from robot.run import run_cli

MODEL_OUTPUT = "testbench2robotframework/model.py"


@task
def generate_model(c: Context, input="openapi.yml") -> None:
    """Regenerates model.py from an OpenAPI spec and injects __VERSION__."""
    if not Path(input).exists():
        raise FileNotFoundError(f"OpenAPI spec not found: {input}")
    c.run(f"datamodel-codegen --input {input}")
    with open(input, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"version:\s*['\"]?([^'\"\n]+)", content)
    version = match.group(1).strip() if match else "unknown"
    model_path = Path(MODEL_OUTPUT)
    model_content = model_path.read_text(encoding="utf-8")
    # Inject __VERSION__
    model_content = model_content.replace(
        "from __future__ import annotations",
        f'from __future__ import annotations\n\n__VERSION__ = "{version}"',
    )
    # datamodel-codegen generates `field: Literal["X"]` without a default, which
    # violates the dataclass rule that non-default fields can't follow default fields.
    # Using field(default=..., init=False) so inherited classes (where Python preserves
    # the parent field's position in the MRO dict) don't break either.
    model_content = model_content.replace(
        "from dataclasses import dataclass\n",
        "from dataclasses import dataclass, field\n",
    )
    model_content = re.sub(
        r'(\w+): (Literal\["([^"]+)"\])(\s*$)',
        r'\1: \2 = field(default="\3", init=False)\4',
        model_content,
        flags=re.MULTILINE,
    )
    model_path.write_text(model_content, encoding="utf-8")
    print(f"Generated {MODEL_OUTPUT} with __VERSION__ = '{version}'")


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
