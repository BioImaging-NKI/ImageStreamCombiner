import logging
import sys
from pathlib import Path
from PyQt6 import QtWidgets as qtw
from ui import mainwidget
from combine_imagestream_files import processzip


class ImageXpressConverter(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ImageStream Combiner")
        self.mainwidget = MainWidget(self)
        self.resize(500, 300)
        self.setCentralWidget(self.mainwidget)
        logging.getLogger().addHandler(self.mainwidget)
        logging.getLogger().setLevel(logging.INFO)

    def closeEvent(self, event):
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])


class MainWidget(qtw.QWidget, logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = mainwidget()
        self.ui.setupUi(self)
        self.ui.run_btn.clicked.connect(self.run)
        self.ui.in_btn.clicked.connect(self.setin)
        self.pth_in = Path('')

    def run(self):
        self.ui.log_txt.appendPlainText('Starting converting files...')
        processzip(self.pth_in)
        self.ui.log_txt.appendPlainText('Finished converting')

    def setin(self):
        file = qtw.QFileDialog.getOpenFileName(self, "Set Zip File", "", "*.zip")
        self.pth_in = Path(file[0])
        self.updateui()

    def updateui(self):
        self.ui.in_lbl.setText(str(self.pth_in))

    def emit(self, record):
        msg = self.format(record)
        self.ui.log_txt.appendPlainText(msg)


def main():
    app = qtw.QApplication(sys.argv)
    main_program = ImageXpressConverter()
    main_program.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
