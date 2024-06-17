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

    def __str__(self) -> str:
        return self.zipfile.stem

    def loadfile(self, zipfile: Path | str) -> None:
        self.zipfile = Path(zipfile)
        self.datasets = {}
        with ZipFile(self.zipfile, "r") as archive:
            for file in archive.namelist():
                if file[-1] == r"/":  # it is a folder
                    pass
                else:
                    if (
                            len(file.split(r"/")) != 2
                    ):  # File is not in a subfolder of the root. Ignore.
                        continue
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

    def writetiffs(
            self,
            folder: Path | str,
            pixelsize: float,
            logger: logging.Logger = logging.getLogger("isz"),
    ) -> None:
        logger.info(f"Writing tiffile for {self}")
        with ZipFile(self.zipfile, "r") as archive:
            for datasetname in self.datasets:
                logger.info(f"Writing tiffile for {datasetname}")
                dataset = self.datasets[datasetname]
                channels = dataset.getvalidchannels()
                if len(channels) == 0:
                    logger.warning(f"No valid channels for {datasetname}")
                    continue
                # Getting Median/Size/datatype
                mw = 0
                mh = 0
                medians = np.zeros(
                    (len(dataset.groupedfiles), len(channels)),
                    dtype=float,
                )
                logging.getLogger("tifffile").setLevel(
                    logging.ERROR
                )  # otherwise you get many "FILLORDER" errors.
                checkdatatype = True
                clearfiles = []
                for i, file in enumerate(dataset.groupedfiles):  # Each cell
                    skipfile = False
                    for j, channel in enumerate(channels):  # Each channel
                        if channel.index not in dataset.groupedfiles[file]:
                            logger.error(f"{file} does not have {channel.index}. Skipping file.")
                            skipfile = True
                    if skipfile:
                        clearfiles.append(file)
                        continue
                    for j, channel in enumerate(channels):  # Each channel
                        with TiffFile(
                                archive.open(
                                    f"{dataset}/{file}_Ch{channel.index}{self.suffix}"
                                )
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
                for clearfile in clearfiles:
                    del dataset.groupedfiles[clearfile]
                dataset.medians = np.median(medians, axis=0)
                dataset.size = (mw, mh)

                # Writing Tiff
                outpth = Path(folder, f"{dataset}.tif")
                outpth.parent.mkdir(parents=True, exist_ok=True)

                data = np.zeros(
                    (
                        len(dataset.groupedfiles),
                        dataset.getnvalidchannels(),
                        dataset.size[0],
                        dataset.size[1],
                    ),
                    dtype=dataset.datatype,
                )
                for i, file in enumerate(dataset.groupedfiles):
                    for j, channel in enumerate(channels):
                        with TiffFile(
                                archive.open(
                                    f"{dataset}/{file}_Ch{channel.index}{self.suffix}"
                                )
                        ) as tfile:
                            page = tfile.pages[0]
                            data[i, j, :, :] = dataset.medians[j]
                            w = page.shape[0]
                            h = page.shape[1]
                            offsetx = (dataset.size[0] - w) // 2
                            offsety = (dataset.size[1] - h) // 2
                            data[i, j, offsetx: offsetx + w, offsety: offsety + h] = (
                                page.asarray()
                            )

                # find ranges for each channel
                ranges = []
                for ch in range(data.shape[1]):
                    ranges.append(dataset.medians[ch])
                    ranges.append(data[:, ch, :, :].max())
                medians_str = "\n" + ",".join([str(int(x)) for x in dataset.medians])
                channelnames = [str(x) for x in dataset.getvalidchannels()]
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
                        "Labels": channelnames * len(dataset.groupedfiles),
                        "Ranges": [ranges],
                        "Properties": {"Medians": medians_str},
                    },
                )
