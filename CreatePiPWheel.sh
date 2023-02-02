#!/bin/bash
check-manifest --update
rm -f dist/*.*
python setup.py bdist_wheel sdist
twine check dist/*
read -n 1
twine upload dist/*