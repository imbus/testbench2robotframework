
check-manifest --update
del dist\* /Q /S /F
python setup.py bdist_wheel sdist
twine check dist\*
pause
twine upload dist\*

