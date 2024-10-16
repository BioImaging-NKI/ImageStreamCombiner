The .ui files were designed with `pyside6-designer`

They were converted with to .py files with the same name.
* Windows: `venv\Scripts\pyside6-uic.exe -o ui\form.py ui\form.ui`
* Linux: `.venv/bin/pyside6-uic -o ui/form.py ui/form.ui`


! Never ! edit the generated .py files, but edit the .ui files if you want to change the ui.