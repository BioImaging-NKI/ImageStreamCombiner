import logging
from PyQt6 import QtCore, QtWidgets


class QTextEditLogger(QtWidgets.QPlainTextEdit):
    log = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        QtCore.QObject.__init__(self)
        self.setReadOnly(True)
        self.log.connect(self.myAppendPlainText)

    def myAppendPlainText(self, text):
        self.appendPlainText(text)
        self.repaint()


class QLogHandler(logging.Handler):
    def __init__(self, emitter):
        super().__init__()
        self._emitter = emitter

    @property
    def emitter(self):
        return self._emitter

    def emit(self, record):
        msg = self.format(record)
        self.emitter.log.emit(msg)


def configure_logging(*, handlers):
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s",
        handlers=handlers,
    )
