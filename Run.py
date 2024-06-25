import sys
from PyQt5 import QtWidgets

import DocWidgets



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DocWidgets.ReaderWidget()
    window.show()
    sys.exit(app.exec_())
