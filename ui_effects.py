from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QBrush


def enable_transparency(widget, color=QColor(30, 30, 30, 200), corner_radius=12):
    widget.setAttribute(Qt.WA_TranslucentBackground)
    widget.setWindowFlags(widget.windowFlags() | Qt.FramelessWindowHint)

    def paintEvent(event):
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.Antialiasing)

        if color.alpha() > 0:
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(widget.rect(), corner_radius, corner_radius)

    widget.paintEvent = paintEvent