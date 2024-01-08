# Contributing
## Setting up project for the first time
1. Write all dependencies into setup.cfg (install_requires and extras_require).
2. Create venv (python -m venv .venv) and activate it (".venv\scripts\activate" or "source .venv/bin/activate")
3. Update pip (python -m pip install -U pip)
3. Install pip-tools (pip install pip-tools)
4. Update/Create `requirements.txt` (when dependencies have been updated in setup.cfg)
    - with Development dependencies
        > pip-compile --extra dev setup.cfg
    - or only with Runtime dependencies
        > pip-compile setup.cfg
5. Install dependencies (pip install -U -r requirements.txt)
6. Install project into local venv (pip install -e .[extra])


## Generate documentation in Word format
 [Install Pandoc](https://pandoc.org/installing.html)

```shell
pandoc -s README.md -M title="imbus TestBench - Robot Code Generator" -M subtitle=Benutzerhandbuch -M toc-title=Inhaltsverzeichnis --toc -o Benutzerhandbuch.docx
```




