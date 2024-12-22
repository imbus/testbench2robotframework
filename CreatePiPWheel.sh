#!/bin/bash
check-manifest --update
python -m build
twine check dist\*
twine upload dist/*
