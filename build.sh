#!/usr/bin/env bash

pyside6-rcc resources.rcc -o resources_rc.py
uv run pyinstaller --onefile --windowed --add-data 'resources_rc.py:.' --add-data 'templates/PyProject.json:.' main.py --name PyProject
cp dist/PyProject /public/devel/25-26/PyProject
cp -r templates/ /public/devel/25-26/PyProject


cp pyproject.png  /public/devel/25-26/PyProject
