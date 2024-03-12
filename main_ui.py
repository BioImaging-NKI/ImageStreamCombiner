import logging
import sys
from pathlib import Path
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
import toml
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent, QColor

from combine_imagestream_files.dataset import DataSet, Channel
from combine_imagestream_files.imagestreamzip import ImageStreamZip
from ui import MainWidget
from ui.customwidgets import QLogHandler, configure_logging


class ImageStreamCombiner(QtW.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ImageStream Combiner")
        self.mainwidget = MyMainWidget(self)
        self.setCentralWidget(self.mainwidget)
        self.logger = logging.getLogger(__name__)
        configure_logging(
            handlers=[
                logging.FileHandler("debug.log", mode="w"),
                logging.StreamHandler(),
                QLogHandler(self.mainwidget.ui.tel_logging),
            ]
        )
        self.logger.setLevel(logging.INFO)
        self.settings = QSettings("NKI-AVL", "CombineImageStreamFiles")
        self.logger.info("ImageStream Combiner Initialized...")
        self._restorestate()

    def _restorestate(self):
        if self.settings.value("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())


class MyMainWidget(QtW.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = MainWidget()
        self.ui.setupUi(self)
        self.logger = logging.getLogger(__name__)
        configure_logging(
            handlers=[
                logging.FileHandler("debug.log", mode="w"),
                logging.StreamHandler(),
                QLogHandler(self.ui.tel_logging),
            ]
        )
        self.logger.setLevel(logging.INFO)
        self.settings = QSettings("NKI-AVL", "CombineImageStreamFiles")
        self.current_dir = Path(Path.cwd())
        self.ui.pb_run.clicked.connect(self.run)
        self.ui.pb_choosezipfile.clicked.connect(self.setin)
        self.ui.lw_datasets.itemClicked.connect(self.datasetclicked)
        self.ui.lw_channels.itemChanged.connect(self.channelchanged)
        self.ui.pb_toalldatasets.clicked.connect(self.toalldatasets)
        self.ui.pb_save.clicked.connect(self.save)
        self.ui.pb_load.clicked.connect(self.load)
        self.isz = ImageStreamZip()
        self._restore_state()
        self.logger.info("Main widget initialized...")

    def _restore_state(self):
        if self.settings.value("current_dir"):
            self.current_dir = Path(self.settings.value("current_dir"))

    def _setcurrentdir(self, pth: Path):
        self.current_dir = pth
        self.settings.setValue("current_dir", str(pth))

    def dragMoveEvent(self, event: QDragMoveEvent):
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urllist = event.mimeData().urls()
            url = Path(str(urllist[0].toLocalFile()))
            self.logger.info(f"Got: {url}")
            if url.suffix == ".zip":
                self._setin(url)
            if url.suffix == ".toml":
                self._load(url)

    def run(self):
        if not self.isz:
            return
        self.logger.info("Start saving tiff files...")
        self.isz.writetiffs(
            self.current_dir, float(self.ui.dsb_pixelsize.value()), self.logger
        )
        self.logger.info("Finished saving tiff files...")

    def save(self):
        if not self.isz:
            return
        currentdataset = self.ui.lw_datasets.item(
            self.ui.lw_datasets.currentRow()
        ).data(256)
        defaultfile = Path(self.current_dir, f"{currentdataset}.toml")
        file = QtW.QFileDialog.getSaveFileName(
            self,
            "Save Channel File",
            str(defaultfile),
            "*.toml",
        )
        channels = {}
        for x in currentdataset.channels:
            channels[str(x.index)] = x.name
        if file[0]:
            tomldata = {"channels": channels}
            with open(file[0], "w") as f:
                toml.dump(tomldata, f)

    def load(self):
        if not self.isz:
            self.logger.info("No Zipfile Loaded...")
            return
        if len(self.ui.lw_datasets.selectedItems()) == 0:
            self.logger.info("No Dataset Selected...")
            return
        file = QtW.QFileDialog.getOpenFileName(
            self, "Load Channel File", str(self.current_dir), "*.toml"
        )
        pth = Path(file[0])
        self._load(pth)

    def _load(self, pth):
        if not self.isz:
            self.logger.info("No Zipfile Loaded...")
            return
        if len(self.ui.lw_datasets.selectedItems()) == 0:
            self.logger.info("No Dataset Selected...")
            return
        if pth.exists():
            currentdataset = self.ui.lw_datasets.item(
                self.ui.lw_datasets.currentRow()
            ).data(
                256
            )  # type: DataSet
            with open(pth, "r") as f:
                data = toml.load(f)
                channels = data["channels"]
            allchannels = []
            for ch in channels:
                allchannels.append(Channel(int(ch), channels[ch]))
            currentdataset.setchannels(allchannels)
            self.datasetclicked(
                self.ui.lw_datasets.item(self.ui.lw_datasets.currentRow())
            )
            self._setcurrentdir(pth.parent)

    def toalldatasets(self):
        if not self.isz:
            return
        currentdataset = self.ui.lw_datasets.item(
            self.ui.lw_datasets.currentRow()
        ).data(256)
        currentchannels = currentdataset.getchannels()
        for ds_name in self.isz.datasets:
            self.isz.datasets[ds_name].channels = []
            for ch in currentchannels:
                self.isz.datasets[ds_name].channels.append(Channel(ch.index, ch.name))

    def datasetclicked(self, item: QtW.QListWidgetItem):
        if not self.isz:
            return
        dataset = item.data(256)  # type: DataSet
        self.ui.lw_channels.clear()
        self.ui.lw_channelnrs.clear()
        for channel in dataset.channels:
            nameitem = QtW.QListWidgetItem(str(channel))
            nameitem.setFlags(nameitem.flags() | QtC.Qt.ItemFlag.ItemIsEditable)
            self.ui.lw_channels.addItem(nameitem)
            nritem = QtW.QListWidgetItem(f"{channel.index}")
            color = QColor(0, 255, 0, 127) if channel else QColor(255, 0, 0, 127)
            nritem.setBackground(color)
            self.ui.lw_channelnrs.addItem(nritem)

    def channelchanged(self, item: QtW.QListWidgetItem):
        if not self.isz:
            return
        currentdataset = self.ui.lw_datasets.item(
            self.ui.lw_datasets.currentRow()
        ).data(256)
        channelindex = self.ui.lw_channels.currentRow()
        channelnr = int(self.ui.lw_channelnrs.item(channelindex).text())
        self.logger.info(f"Channel {channelnr} changed to {item.text()}")
        currentdataset.setchannelname(str(item.text()), channelnr)
        self.datasetclicked(self.ui.lw_datasets.item(self.ui.lw_datasets.currentRow()))

    def setin(self):
        file = QtW.QFileDialog.getOpenFileName(
            self, "Set Zip File", str(self.current_dir), "*.zip"
        )
        if not file[0]:
            self.logger.warning("No ZipFile Selected...")
            return
        pth = Path(file[0])
        self._setin(pth)

    def _setin(self, pth: Path):
        if pth.exists() and pth.suffix == ".zip":
            self.current_dir = pth.parent
            self.isz.loadfile(pth)
            self.ui.l_filein.setText(str(self.isz))
            for x in self.isz.datasets.keys():
                newitem = QtW.QListWidgetItem(
                    f"{x} : ({len(self.isz.datasets[x].groupedfiles)} cells {self.isz.datasets[x].getnchannels()} channels)"
                )
                newitem.setData(256, self.isz.datasets[x])
                self.ui.lw_datasets.addItem(newitem)
            self.ui.lw_datasets.sortItems()
            self._setcurrentdir(pth.parent)
            self.updateui()
        else:
            self.logger.error(f"Cannot load {pth}")

    def updateui(self):
        self.ui.lw_datasets.update()
        self.ui.lw_channels.update()


def main():
    app = QtW.QApplication(sys.argv)
    main_program = ImageStreamCombiner()
    main_program.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
