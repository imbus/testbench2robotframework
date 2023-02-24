# Contributing

## Development Environment Setup

1. Install Python 3.8 and VS Code

2. Open a terminal in this repository

3. Create the virtual environment .venv

    > /path/to/python38/python -m venv .venv

4. Install the dependencies

    > pip install -r requirements.txt

5. [Install Pandoc](https://pandoc.org/installing.html)


## Generate documentation in Word format

```shell
pandoc -s README.md -M title="imbus TestBench - Robot Code Generator" -M subtitle=Benutzerhandbuch -M toc-title=Inhaltsverzeichnis --toc -o Benutzerhandbuch.docx
```


## Build, Install and Run

The package is built using setuptools. The build configuration is defined in `setup.cfg`.

- Build and install the package
    > pip install -e .

- Run the application
    > tb2robot

- Build a pure-Python wheel
    > python setup.py bdist_wheel


## Adding New Dependencies
1. Install pip-tools (to pin dependencies)

    > python -m pip install pip-tools


2. In `setup.cfg` add a package to the corresponding section

    - Development dependencies: `dev` extra under `options.extras_require`

    - Runtime dependencies: `install-requires`

3. Update `requirements.txt`
    - Development dependencies
        > pip-compile --extra dev setup.cfg

    - Runtime dependencies
        > pip-compile setup.cfg

4. Create a commit with `setup.cfg`, `requirements.txt`, `pyproject.toml` explaining why the dependency was added.


## Static Analysis and Code Formatting

Static analysis and code formatting tools are configured in `pyproject.toml`.

### Static Analysis

- `mypy`: static type checker
    * [The mypy configuration file](https://mypy.readthedocs.io/en/stable/config_file.html)

- `pylint`: syntax and code quality checks

    * [Pylint Global options and switches](https://pylint.pycqa.org/en/latest/technical_reference/features.html)

    * [Overview of all Pylint messages](https://pylint.pycqa.org/en/latest/messages/messages_list.html)

    * [Naming Styles](https://pylint.pycqa.org/en/latest/user_guide/options.html)


### Code Formatting

- `black`: Format the code according to a subset of PEP 8
    > black .

- `isort`: Sort the package imports following PEP 8
    > isort .


## Testing

- `pytest` is configured in `pyproject.toml`
    > python -m pytest
