[![Mypy](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/mypy.yml/badge.svg)](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/mypy.yml)
[![Black](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/black.yml/badge.svg)](https://github.com/BioImaging-NKI/ImageStreamCombiner/actions/workflows/black.yml)
# Combine ImageStream Files

## Usage (with user interface)
* Download from [release](https://github.com/BioImaging-NKI/ImageStreamCombiner/releases)

## Usage (commandline interface)
* Clone or download the repository
* `pip install -e .`
* `combine_imagestream_files`

## Building
* `pip install -e .[dev]`
* `pyi-makespec ImageStreamCombiner.py`
* `pyinstaller ImageStreamCombiner.spec`