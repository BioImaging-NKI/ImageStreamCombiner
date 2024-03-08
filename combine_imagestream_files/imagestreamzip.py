import logging
from pathlib import Path
from zipfile import ZipFile
import numpy as np
from tifffile import TiffFile, imwrite
from combine_imagestream_files.dataset import DataSet


class ImageStreamZip:
    def __init__(self, suffix: str = ".ome.tif") -> None:
        self.suffix: str = suffix
        self.zipfile: Path = Path()
        self.datasets: dict[str, DataSet] = {}
        self.loaded: bool = False

    def __bool__(self) -> bool:
        return self.loaded

    def loadfile(self, zipfile: Path | str) -> None:
        self.zipfile = Path(zipfile)
        self.datasets = {}
        with ZipFile(self.zipfile, "r") as archive:
            for file in archive.namelist():
                if file[-1] == r"/":  # it is a folder
                    pass
                else:
                    (folder, name) = file.split(r"/")
                    if name.endswith(self.suffix):
                        if folder not in self.datasets:
                            self.datasets[folder] = DataSet(folder)
                        self.datasets[folder].addfile(
                            name[0: len(name) - len(self.suffix)]
                        )
            for d in self.datasets:
                self.datasets[d].sort()
            self.loaded = True

    def writetiffs(self, folder: Path | str, pixelsize: float):
        self.getinfos()
        with ZipFile(self.zipfile, "r") as archive:
            for datasetname in self.datasets:
                dataset = self.datasets[datasetname]
                outpth = Path(folder, f"{dataset}.tif")
                outpth.parent.mkdir(parents=True, exist_ok=True)

                data = np.zeros(
                    (
                        len(dataset.groupedfiles),
                        dataset.getnchannels(),
                        dataset.size[0],
                        dataset.size[1],
                    ),
                    dtype=dataset.datatype,
                )
                for i, file in enumerate(dataset.groupedfiles):
                    for j, channel in enumerate(dataset.groupedfiles[file]):
                        with TiffFile(
                                archive.open(f"{dataset}/{file}_Ch{channel}{self.suffix}")
                        ) as tfile:
                            page = tfile.pages[0]
                            data[i, j, :, :] = dataset.medians[j]
                            w = page.shape[0]
                            h = page.shape[1]
                            offsetx = (dataset.size[0] - w) // 2
                            offsety = (dataset.size[1] - h) // 2
                            data[i, j, offsetx: offsetx + w, offsety: offsety + h] = page.asarray()

                # find ranges for each channel
                ranges = []
                for ch in range(data.shape[1]):
                    ranges.append(dataset.medians[ch])
                    ranges.append(data[:, ch, :, :].max())
                medians_str = "\n" + ",".join([str(int(x)) for x in dataset.medians])
                imwrite(
                    outpth,
                    data,
                    imagej=True,
                    resolution=(1 / pixelsize, 1 / pixelsize),
                    photometric="minisblack",
                    metadata={
                        "spacing": pixelsize,
                        "unit": "um",
                        "axes": "TCYX",
                        "Labels": dataset.channelnames * len(dataset.groupedfiles),
                        "Ranges": [ranges],
                        "Properties": {"Medians": medians_str},
                    },
                )

    def getinfos(self) -> None:
        with ZipFile(self.zipfile, "r") as archive:
            for datasetname in self.datasets:
                dataset = self.datasets[datasetname]
                mw = 0
                mh = 0
                medians = np.zeros(
                    (len(dataset.groupedfiles), dataset.getnchannels()),
                    dtype=float,
                )
                logging.getLogger("tifffile").setLevel(
                    logging.ERROR
                )  # otherwise you get many "FILLORDER" errors.
                checkdatatype = True
                for i, file in enumerate(dataset.groupedfiles):
                    for j, channel in enumerate(dataset.groupedfiles[file]):
                        with TiffFile(
                                archive.open(f"{dataset}/{file}_Ch{channel}{self.suffix}")
                        ) as tfile:
                            page = tfile.pages[0]
                            if checkdatatype:
                                dataset.datatype = page.asarray().dtype
                                checkdatatype = False
                            if page.shape[0] > mw:
                                mw = page.shape[0]
                            if page.shape[1] > mh:
                                mh = page.shape[1]
                            medians[i, j] = np.median(page.asarray())
                dataset.medians = np.median(medians, axis=0)
                dataset.size = (mw, mh)

    def __str__(self) -> str:
        return str(self.zipfile)
