# group them
from pathlib import Path
from typing import Dict, List


def group(files: List[Path], suffix: str) -> Dict[str, List[int]]:
    grouped_files = {}  # type:Dict[str, List[int]]
    for file in files:
        name = file.name[0 : len(file.name) - len(suffix) - 1]
        nparts = name.split("_")
        ch = int(nparts[-1][2::])  # Ch1 Ch11
        stem = "_".join(nparts[0:-1])
        if stem in grouped_files:
            grouped_files[stem].append(ch)
        else:
            grouped_files[stem] = [ch]
    for k in grouped_files:
        grouped_files[k].sort()
    return grouped_files
