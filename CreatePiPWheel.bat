check-manifest --update
pause
python -m build
pause
twine check dist\*
pause
twine upload dist/*
