from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui     import QFont, QColor
from PyQt5.QtCore    import Qt

def create_floating_text(parent, text="Hello, World!", base_font_size=32, color="#FF66CC"):
    label = QLabel(text, parent)
    label.setStyleSheet(f"""
        QLabel {{
            color: {color};
            background-color: transparent;
        }}
    """)
    label.setAttribute(Qt.WA_TransparentForMouseEvents) 
    label.setAlignment(Qt.AlignCenter)
    label.base_font_size = base_font_size
    label.setFont(QFont("Arial", base_font_size, QFont.Bold))
    label.adjustSize()
    return label