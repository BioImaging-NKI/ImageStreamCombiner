from datetime import datetime
from pathlib import Path
import pandas as pd
from tifffile import TiffFile, imwrite
import numpy as np
from zipfile import ZipFile
from tqdm import tqdm
import logging
from combine_imagestream_files import group

logging.getLogger("tifffile").setLevel(logging.ERROR)
logger = logging.getLogger("combine imagestream files")
logger.setLevel(logging.DEBUG)
start_time = datetime.now()

xlsxfile = Path(
    r"D:\Surfdrive\Shared\Projects\Daniela Thommen\Floris&Christina\new_data\CD45-EPCAM_data_doublets.ods"
)
xlsxdata = {
    "Datasets": pd.read_excel(xlsxfile, sheet_name="Datasets"),
    "Channels": pd.read_excel(xlsxfile, sheet_name="Channels"),
    "Experiment": pd.read_excel(xlsxfile, sheet_name="Experiment"),
}

zipfile = {
    "zippath": Path(xlsxfile.parent, xlsxfile.stem + ".zip"),
    "suffix": "ome.tif",
    "channels": xlsxdata["Channels"],
    "datasets": {},
}

for index, row in xlsxdata["Datasets"].iterrows():
    zipfile["datasets"][row["Name"]] = {
        "pixelsize": float(row["Pixelsize"]),
        "files": [],
    }

with ZipFile(zipfile["zippath"], mode="r") as archive:
    for file in archive.namelist():
        if file[-1] == r"/":  # it is a folder
            pass
        else:
            (folder, name) = file.split(r"/")
            if name.endswith(zipfile["suffix"]):
                zipfile["datasets"][folder]["files"].append(name)

ch = list(zipfile["channels"]["Channel"])
for folder in zipfile["datasets"]:
    files = [Path(x) for x in zipfile["datasets"][folder]["files"]]
    zipfile["datasets"][folder]["grouped_files"] = group(files, zipfile["suffix"])
    remove_keys = []
    for k in zipfile["datasets"][folder]["grouped_files"]:
        if not all(x in zipfile["datasets"][folder]["grouped_files"][k] for x in ch):
            logger.warning(
                f"{k} only has {zipfile['datasets'][folder]['grouped_files'][k]}"
            )
            remove_keys.append(k)
    logger.warning(f"REMOVING {len(remove_keys)} CELLS!")
    for k in remove_keys:
        zipfile["datasets"][folder]["grouped_files"].pop(k)

data = zipfile["datasets"][folder]
datatype = None
with ZipFile(zipfile["zippath"], mode="r") as archive:
    with TiffFile(archive.open(folder + r"/" + data["files"][0])) as tif:
        datatype = tif.pages[0].asarray().dtype

with ZipFile(zipfile["zippath"], mode="r") as archive:
    for folder in zipfile["datasets"]:
        data = zipfile["datasets"][folder]
        # <find median>
        mw = 0
        mh = 0
        medians = np.zeros(
            (len(data["grouped_files"]), len(zipfile["channels"]["Channel"])),
            dtype=float,
        )
        for i, k in tqdm(enumerate(data["grouped_files"])):
            for j, ch in enumerate(zipfile["channels"]["Channel"]):
                filename = k + "_Ch" + str(ch) + "." + zipfile["suffix"]
                with TiffFile(archive.open(folder + r"/" + filename)) as tfile:
                    page = tfile.pages[0]
                    if page.shape[0] > mw:
                        mw = page.shape[0]
                    if page.shape[1] > mh:
                        mh = page.shape[1]
                    medians[i, j] = np.median(page.asarray())
        medians = np.median(medians, axis=0)
        # </find median>
        data["medians"] = medians
        data["dataset"] = np.zeros(
            (len(data["grouped_files"]), len(zipfile["channels"]["Channel"]), mw, mh),
            dtype=datatype,
        )
        for i, k in tqdm(enumerate(data["grouped_files"])):
            for j, ch in enumerate(zipfile["channels"]["Channel"]):
                filename = k + "_Ch" + str(ch) + "." + zipfile["suffix"]
                with TiffFile(archive.open(folder + r"/" + filename)) as tfile:
                    tdata = tfile.pages[0]
                    w = tdata.shape[0]
                    h = tdata.shape[1]
                    offsetx = (mw - w) // 2
                    offsety = (mh - h) // 2
                    data["dataset"][i, j, :, :] = medians[j]
                    data["dataset"][
                        i, j, offsetx : offsetx + w, offsety : offsety + h
                    ] = tdata.asarray()

for folder in zipfile["datasets"]:
    data = zipfile["datasets"][folder]
    pixelsize = data["pixelsize"]
    channelnames = [x for x in zipfile["channels"]["Name"]]
    outpth = Path(zipfile["zippath"].parent, "merged_tiffs", folder + ".tif")
    outpth.parent.mkdir(parents=True, exist_ok=True)
    # find ranges for each channel
    ranges = []
    for ch in range(data["dataset"].shape[1]):
        ranges.append(medians[ch])
        ranges.append(data["dataset"][:, ch, :, :].max())
    medians_str = "\n" + ",".join([str(int(x)) for x in data["medians"]])
    imwrite(
        outpth,
        data["dataset"],
        imagej=True,
        resolution=(1 / pixelsize, 1 / pixelsize),
        photometric="minisblack",
        metadata={
            "spacing": pixelsize,
            "unit": "um",
            "axes": "TCYX",
            "Labels": channelnames * data["dataset"].shape[0],
            "Ranges": [ranges],
            "Properties": {"Medians": medians_str},
        },
    )

end_time = datetime.now()
logger.warning(f"Runtime: {end_time - start_time}")
