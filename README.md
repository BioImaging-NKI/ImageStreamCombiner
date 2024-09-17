[![Mypy](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/mypy.yml/badge.svg)](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/mypy.yml)
[![Black](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/black.yml/badge.svg)](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/black.yml)
# Combine ImageStream Files

## Usage (with user interface)
* Download from [release](https://github.com/BioImaging-NKI/ImageStreamCombiner/releases)

or

* Install: `pip install .[gui]`
* [Generate ui](/ui)
* Run: `python ImageStreamCombiner.py`

## Usage (commandline interface)
* Clone or download the repository
* `pip install .`
* `combine_imagestream_files -h`

## Building standalone executable
* `pip install .[build]`
* [Generate ui](/ui)
* `pyi-makespec ImageStreamCombiner.py`
* `pyinstaller ImageStreamCombiner.spec`

## Editable install
* `pip install meson-python meson ninja`
* `pip install --no-build-isolation --editable .[dev]`