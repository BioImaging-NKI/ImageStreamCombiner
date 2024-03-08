import numpy as np


class DataSet:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.groupedfiles: dict[str, list[int]] = {}  # channels for each cell
        self.channelnames: list[str] = []  # name for each channel
        self.medians: list[int] = []  # median for each channel
        self.size = (0, 0)  # max width and max height
        self.datatype = np.uint8

    def __str__(self) -> str:
        return self.name

    def setchannelnames(self, channelnames: list[str]) -> None:
        self.channelnames = channelnames

    def addchannelname(self, idx, name):
        if len(self.channelnames) <= idx:
            self.channelnames.extend('' for _ in range(idx - len(self.channelnames)+1))
        self.channelnames[idx] = name

    def addfile(self, file: str) -> None:
        nparts = file.split("_")
        ch = int(nparts[-1][2::])  # Ch1 Ch11
        self.addchannelname(ch - 1, f'--')
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
                print(
                    f"{k} only has {len(self.groupedfiles[k])} channels instead of {nch}"
                )
                allsamelength = False
        return allsamelength

    def getchannels(self) -> list[int]:
        for k in self.groupedfiles:
            return self.groupedfiles[k]
        return []

    def getnchannels(self) -> int:
        for k in self.groupedfiles:
            return len(self.groupedfiles[k])
        return -1
