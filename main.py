from PyQt5.QtWidgets import QApplication
from window_base import FramelessResizableWindow
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FramelessResizableWindow()
    window.show()
    sys.exit(app.exec_())