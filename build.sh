#!/usr/bin/env bash

pyside6-rcc resources.rcc -o resources_rc.py
uv run pyinstaller --onefile --windowed --add-data 'resources_rc.py:.' --add-data 'PyProject.json:.' main.py --name PyProject
cp dist/PyProject /public/devel/25-26/PyProject
cp PyProject.json /public/devel/25-26/PyProject
cp MainDialog.ui /public/devel/25-26/PyProject


# cp appsereicon.png  /public/devel/25-26/AppsEre
# cp AppsEre.desktop /public/devel/25-26/AppsEre
