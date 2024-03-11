from typing import Any

import numpy as np


class Channel:
    def __init__(self, index: int = -1, name: str = "") -> None:
        if name == "--":
            name = ""
        self.name = name  # name of channel (empty if present in dataset, but not used)
        self.index = index  # index of channel (starts at 1, like the files)

    def __str__(self) -> str:
        if self.name:
            return self.name
        else:
            return "--"

    def __bool__(self) -> bool:
        return len(self.name) > 0

    def __lt__(self, other: "Channel") -> bool:
        return self.index < other.index


class DataSet:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.groupedfiles: dict[str, list[int]] = {}  # channels for each cell
        self.channels: list[Channel] = []  # name for each channel
        self.medians: list[int] = []  # median for each channel
        self.size = (0, 0)  # max width and max height
        self.datatype: np.dtype[Any]

    def __str__(self) -> str:
        return self.name

    def setchannels(self, channelnames: list[str]) -> None:
        self.channels = [Channel(i + 1, x) for i, x in enumerate(channelnames)]

    def setchannelname(self, channelname: str, index: int) -> None:
        channel = [x for x in self.channels if x.index == index]
        if len(channel) == 1:
            channel[0].name = channelname

    def addfile(self, file: str) -> None:
        nparts = file.split("_")
        ch = int(nparts[-1][2::])  # Ch1 Ch11
        if ch not in [x.index for x in self.channels]:
            self.channels.append(Channel(ch, ""))
            self.channels.sort()
        stem = "_".join(nparts[0:-1])
        if stem in self.groupedfiles:
            self.groupedfiles[stem].append(ch)
        else:
            self.groupedfiles[stem] = [ch]

    def sort(self) -> None:
        for k in self.groupedfiles:
            self.groupedfiles[k].sort()

    def checkchannels(self, channels: list[Channel]) -> bool:
        """
        Do the channels exist for all cells
        :param channels:
        :return:
        """
        allexist = True
        for k in self.groupedfiles:
            if not all(x.index in self.groupedfiles[k] for x in channels):
                print(f"{k} only has {self.groupedfiles[k]}")
                allexist = False
        return allexist

    def getvalidchannels(self) -> list[Channel]:
        return [x for x in self.channels if x]

    def getchannels(self) -> list[Channel]:
        return [x for x in self.channels]

    def getnchannels(self) -> int:
        return len(self.getchannels())

    def getnvalidchannels(self) -> int:
        return len(self.getvalidchannels())
