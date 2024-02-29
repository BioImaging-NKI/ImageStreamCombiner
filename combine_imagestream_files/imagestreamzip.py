import logging
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from tifffile import TiffFile


class ImageStreamZip:
    def __init__(self, suffix: str = '.ome.tif') -> None:
        self.suffix = suffix
        self.zipfile = Path()
        self.datasets = {}
        self.filename = ''

    def loadfile(self, zipfile: Path | str) -> None:
        self.filename = Path(zipfile)
        self.datasets = {}
        archive = ZipFile(self.filename, 'r')
        for file in archive.namelist():
            if file[-1] == r"/":  # it is a folder
                pass
            else:
                (folder, name) = file.split(r"/")
                if name.endswith(self.suffix):
                    if folder not in self.datasets:
                        self.datasets[folder] = DataSet(folder)
                    self.datasets[folder].addfile(name[0: len(name) - len(self.suffix)])
        for d in self.datasets:
            self.datasets[d].sort()

    def getinfos(self) -> None:
        for dataset in self.datasets:
            self.getinfo(self.datasets[dataset])

    def getinfo(self, dataset: "Dataset") -> None:
        archive = ZipFile(self.filename, 'r')
        mw = 0
        mh = 0
        medians = np.zeros(
            (len(dataset.groupedfiles), dataset.getnchannels()),
            dtype=float,
        )
        logging.getLogger("tifffile").setLevel(logging.ERROR)  # otherwise you get many "FILLORDER" errors.
        for i, file in enumerate(dataset.groupedfiles):
            for j, channel in enumerate(dataset.groupedfiles[file]):
                with TiffFile(archive.open(f"{dataset}/{file}_Ch{channel}{self.suffix}")) as tfile:
                    page = tfile.pages[0]
                    if page.shape[0] > mw:
                        mw = page.shape[0]
                    if page.shape[1] > mh:
                        mh = page.shape[1]
                    medians[i, j] = np.median(page.asarray())
        dataset.medians = np.median(medians, axis=0)
        dataset.size = (mw, mh)

    def __str__(self) -> str:
        return str(self.filename)


class DataSet:
    def __init__(self, name) -> None:
        self.name = name
        self.groupedfiles = {}  # channels for each image
        self.channelnames = []  # name for each channel
        self.medians = []   # median for each channel
        self.size = (0, 0)  # max width and height

    def __str__(self)->str:
        return self.name
    def setchannelnames(self, channelnames: list[str]) -> None:
        self.channelnames = channelnames

    def addfile(self, file: str) -> None:
        nparts = file.split("_")
        ch = int(nparts[-1][2::])  # Ch1 Ch11
        stem = "_".join(nparts[0:-1])
        if stem in self.groupedfiles:
            self.groupedfiles[stem].append(ch)
        else:
            self.groupedfiles[stem] = [ch]

    def sort(self) -> None:
        for k in self.groupedfiles:
            self.groupedfiles[k].sort()

    def checkchannels(self, channels: list[int]) -> bool:
        allexist = True
        for k in self.groupedfiles:
            if not all(x in self.groupedfiles[k] for x in channels):
                print(f"{k} only has {self.groupedfiles[k]}")
                allexist = False
        return allexist

    def checknchannels(self) -> bool:
        allsamelength = True
        nch = self.getnchannels()
        for k in self.groupedfiles:
            if len(self.groupedfiles[k]) != nch:
                print(f"{k} only has {len(self.groupedfiles[k])} channels instead of {nch}")
                allsamelength = False
        return allsamelength

    def getchannels(self) -> dict[str:list[int]]:
        for k in self.groupedfiles:
            return self.groupedfiles[k]

    def getnchannels(self) -> int:
        for k in self.groupedfiles:
            return len(self.groupedfiles[k])
