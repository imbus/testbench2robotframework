# Contributing

## Setting up project for the first time

1. Create venv and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\scripts\activate     # Windows
   ```
2. Install project with dev dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Release process

This project is published with `flit`.

1. Prepare the release
   1. Make sure you are on the correct branch and your working tree is clean.
   2. Update the version in `testbench2robotframework/__init__.py` (`__version__`).
   3. Commit the version change (and other release-related updates).
2. Build artifacts locally (without upload)
   ```bash
   flit build
   ```
   This creates source and wheel distributions in `dist/` so you can verify the build output.
3. Publish to PyPI
   ```bash
   flit publish
   ```
   `flit publish` builds, validates, and uploads the package.
4. Verify the release
   1. Confirm the new version is visible on PyPI.
   2. Create and push a git tag for the released version (for example `v1.1.0`).

If you only need to validate packaging locally, use `flit build` and skip the publish step.

## Updating the data model

`testbench2robotframework/model.py` is generated from the TestBench OpenAPI spec using [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator).

1. Download the OpenAPI YAML from the TestBench Swagger documentation (e.g. `openapi.yml`).
2. Generate the model (settings are in `pyproject.toml` under `[tool.datamodel-codegen]`):
   ```bash
   invoke generate-model --input openapi.yml
   ```
   This runs `datamodel-codegen` and injects `__VERSION__` from the spec's `info.version` field into `model.py`.
3. Review the generated file
