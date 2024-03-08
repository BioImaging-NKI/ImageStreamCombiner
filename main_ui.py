import logging
import sys
from pathlib import Path
from PyQt6 import QtWidgets as QtW
from PyQt6 import QtCore as QtC
import toml
from combine_imagestream_files.dataset import DataSet
from combine_imagestream_files.imagestreamzip import ImageStreamZip
from ui import MainWidget


class ImageStreamCombiner(QtW.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ImageStream Combiner")
        self.mainwidget = MyMainWidget(self)
        # self.resize(750, 400)
        self.setCentralWidget(self.mainwidget)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(self.mainwidget)
        self.logger.setLevel(logging.INFO)
        self.logger.info("ImageStream Combiner Initialized...")

    def closeEvent(self, event):
        self.logger.removeHandler(self.logger.handlers[0])


class MyMainWidget(QtW.QWidget, logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = MainWidget()
        self.ui.setupUi(self)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(self)
        self.logger.setLevel(logging.INFO)
        self.current_dir = Path(r"c:\Temp\Sofia")
        self.ui.pb_run.clicked.connect(self.run)
        self.ui.pb_choosezipfile.clicked.connect(self.setin)
        self.ui.lw_datasets.itemClicked.connect(self.datasetclicked)
        self.ui.lw_channels.itemChanged.connect(self.channelchanged)
        self.ui.pb_toallchannels.clicked.connect(self.toallchannels)
        self.ui.pb_save.clicked.connect(self.save)
        self.ui.pb_load.clicked.connect(self.load)
        self.isz = ImageStreamZip()
        self.logger.info("Main widget initialized...")

    def run(self):
        if not self.isz:
            return
        self.logger.info("Starting converting files...")
        self.isz.writetiffs(self.current_dir, float(self.ui.dsb_pixelsize.value()))
        self.logger.info("Finished converting files...")

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
        if file[0]:
            tomldata = {"channelnames": currentdataset.channelnames[:]}
            with open(file[0], "w") as f:
                toml.dump(tomldata, f)

    def load(self):
        if not self.isz:
            return
        file = QtW.QFileDialog.getOpenFileName(
            self, "Load Channel File", str(self.current_dir), "*.toml"
        )
        pth = Path(file[0])
        if pth.exists():
            currentdataset = self.ui.lw_datasets.item(
                self.ui.lw_datasets.currentRow()
            ).data(256)
            with open(pth, "r") as f:
                channelnames = toml.load(f)
            currentdataset.channelnames = channelnames["channelnames"]
            self.datasetclicked(
                self.ui.lw_datasets.item(self.ui.lw_datasets.currentRow())
            )

    def toallchannels(self):
        if not self.isz:
            return
        currentdataset = self.ui.lw_datasets.item(
            self.ui.lw_datasets.currentRow()
        ).data(256)
        for ds_name in self.isz.datasets:
            self.isz.datasets[ds_name].channelnames = currentdataset.channelnames[:]

    def datasetclicked(self, item: QtW.QListWidgetItem):
        if not self.isz:
            return
        dataset = item.data(256)  # type: DataSet
        self.ui.lw_channels.clear()
        self.ui.lw_channelnrs.clear()
        for i, chname in enumerate(dataset.channelnames):
            nameitem = QtW.QListWidgetItem(chname)
            nameitem.setFlags(nameitem.flags() | QtC.Qt.ItemFlag.ItemIsEditable)
            self.ui.lw_channels.addItem(nameitem)
            nritem = QtW.QListWidgetItem(f"{i + 1}")
            self.ui.lw_channelnrs.addItem(nritem)

    def channelchanged(self, item: QtW.QListWidgetItem):
        if not self.isz:
            return
        currentdataset = self.ui.lw_datasets.item(
            self.ui.lw_datasets.currentRow()
        ).data(256)
        channelindex = self.ui.lw_channels.currentRow()
        if item.text():
            currentdataset.channelnames[channelindex] = item.text()
        else:
            currentdataset.channelnames[channelindex] = "--"

    def setin(self):
        file = QtW.QFileDialog.getOpenFileName(
            self, "Set Zip File", str(self.current_dir), "*.zip"
        )
        if not file[0]:
            return
        pth = Path(file[0])
        if pth.exists():
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
        else:
            print("ERROR")
        self.updateui()

    def updateui(self):
        self.ui.lw_datasets.update()
        self.ui.lw_channels.update()

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self.ui.pte_log.appendPlainText(msg)
        self.ui.pte_log.update()

    def closeEvent(self, event):
        self.logger.removeHandler(self.logger.handlers[0])


def main():
    app = QtW.QApplication(sys.argv)
    main_program = ImageStreamCombiner()
    main_program.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
