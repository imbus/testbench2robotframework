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

## Building and publishing

```bash
check-manifest --update
python -m build
twine check dist/*
twine upload dist/*
```

## Updating the data model

`testbench2robotframework/model.py` is generated from the TestBench OpenAPI spec using [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator).

1. Download the OpenAPI YAML from the TestBench Swagger documentation (e.g. `openapi.yml`).
2. Generate the model (settings are in `pyproject.toml` under `[tool.datamodel-codegen]`):
    ```bash
    invoke generate-model --input openapi.yml
    ```
   This runs `datamodel-codegen` and injects `__VERSION__` from the spec's `info.version` field into `model.py`.
3. Review the generated file
