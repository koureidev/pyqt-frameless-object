from cmath import rect
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore    import Qt, QRect, QPoint
from PyQt5.QtGui     import QCursor, QColor, QFont, QPainter, QPalette
from PyQt5.QtWidgets import QMenu, QAction, QInputDialog, QMessageBox
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtCore import QSize, QPointF
import os
from PyQt5.QtGui import QFontMetrics
from ui_effects      import enable_transparency
from log import log_redimensionamento, log_troca_texto
import sys
import traceback

sys.stdout = open("debug_log.txt", "w", encoding="utf-8")

def quebrar_texto_longo(texto, max_chars_sem_espaco=20):
    resultado = [texto[i:i+max_chars_sem_espaco] for i in range(0, len(texto), max_chars_sem_espaco)]
    return "\n".join(resultado)

    for palavra in palavras:
        if len(palavra) <= max_chars_sem_espaco:
            resultado.append(palavra)
        else:
            partes = [palavra[i:i+max_chars_sem_espaco] for i in range(0, len(palavra), max_chars_sem_espaco)]
            resultado.extend(partes)

    return "\n".join(resultado)

def log_debug_etapas(texto, tem_quebra, largura, altura, largura_final, altura_final, mudou_tamanho):
    with open("debug_log.txt", "a", encoding="utf-8") as f:
        f.write("\n==========\n")
        f.write(f"Texto: {repr(texto)}\n")
        f.write(f"Tem quebra? {tem_quebra}\n")
        f.write(f"Largura do texto (sem margem): {largura}\n")
        f.write(f"Altura do texto (sem margem): {altura}\n")
        f.write(f"Largura final (com margem): {largura_final}\n")
        f.write(f"Altura final (com margem): {altura_final}\n")
        f.write(f"Janela redimensionada? {'SIM' if mudou_tamanho else 'NÃO'}\n")

class ScalableLabel(QLabel):
    def __init__(self, parent, text, base_font_size, color):
        super().__init__(text, parent)
        self.base_font_size = base_font_size
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: transparent;
            }}
        """)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", base_font_size, QFont.Bold))
        self.adjustSize()

    def setScales(self, sx, sy):
        self.scale_x = sx
        self.scale_y = sy
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.save()
        painter.scale(self.scale_x, self.scale_y)

        font = self.font()
        painter.setFont(font)
        fm = QFontMetrics(font)

        margem_top   = int(self.base_font_size * 0.07)
        margem_bot   = int(self.base_font_size * 0.04)
        margem_left  = int(self.base_font_size * 0.04)

        lines = self.text().split("\n")
        line_height  = fm.lineSpacing()
        total_h      = len(lines) * line_height

        area_h = self.height() / self.scale_y
        top_corr = fm.tightBoundingRect(lines[0]).top()

        if total_h + margem_top + margem_bot <= area_h:
            y0 = area_h - total_h - margem_bot - top_corr
        else:
            y0 = margem_top - top_corr

        for idx, linha in enumerate(lines):
            x = margem_left - fm.tightBoundingRect(linha).left()
            y = y0 + idx * line_height
            painter.drawText(int(x), int(y), linha)

        painter.restore()

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        lines = self.text().split("\n")
        widths = [fm.horizontalAdvance(linha) for linha in lines]
        largura_texto = max(widths) if widths else 0
        altura_texto = len(lines) * fm.lineSpacing()
        
        mt = int(self.base_font_size * 0.07)
        mb = int(self.base_font_size * 0.04)
        ml = int(self.base_font_size * 0.04)
        mr = int(self.base_font_size * 0.04)
        
        largura = largura_texto + ml + mr
        altura = altura_texto + mt + mb
        return QSize(int(largura * self.scale_x), int(altura * self.scale_y))

class FramelessResizableWindow(QWidget):
    MARGIN = 8

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMouseTracking(True)

        self._pressed = False
        self._press_pos = None
        self._resize_direction = []
        self._moving = False

        enable_transparency(self, color=QColor(0, 0, 0, 1))

        self.text_label = ScalableLabel(self, text="q", base_font_size=32, color="#FF66CC")
        self._last_text = self.text_label.text()
        self._base_size_cache = {}
        self._update_base_text_size()
        self._set_window_to_label()

    def _update_base_text_size(self):
        self.text_label.setFont(QFont("Arial", self.text_label.base_font_size, QFont.Bold))
        metrics = QFontMetrics(self.text_label.font())
        text = self.text_label.text()
        br = metrics.tightBoundingRect(text)
        mt = int(self.text_label.base_font_size * 0.07)
        mb = int(self.text_label.base_font_size * 0.04)
        ml = int(self.text_label.base_font_size * 0.04)
        mr = int(self.text_label.base_font_size * 0.04)

        width = br.width() + ml + mr
        height = br.height() + mt + mb
        self._base_text_size = QSize(width, height)
        self.setMinimumSize(self._base_text_size)

    def _set_window_to_label(self):
        label_w = int(self._base_text_size.width() * self.text_label.scale_x)
        label_h = int(self._base_text_size.height() * self.text_label.scale_y)
        self.text_label.setFixedSize(label_w, label_h)
        self.setGeometry(self.x(), self.y(), label_w, label_h)
        self.text_label.move(0, 0)

    def resizeEvent(self, event):
        if not self._base_text_size or self._base_text_size.width() == 0:
            return
        base_w = self._base_text_size.width()
        base_h = self._base_text_size.height()
        sx = self.width() / base_w
        sy = self.height() / base_h

        self.text_label.setScales(sx, sy)
        self.text_label.setFixedSize(self.size())

    def update_text_preserving_scale(self, novo_texto):
        texto_antigo = self._last_text or ""
        sx, sy = self.text_label.scale_x, self.text_label.scale_y

        self.text_label.setScales(1, 1)
        self.text_label.setFont(QFont("Arial", self.text_label.base_font_size, QFont.Bold))
        self.text_label.setText(novo_texto)
        QApplication.processEvents()

        def tem_quebra(t):
            return "\n" in t

        if novo_texto.strip() == texto_antigo.strip():
            self.text_label.setScales(sx, sy)
            log_troca_texto(novo_texto + " (sem alterações)")
            return

        fm = QFontMetrics(self.text_label.font())
        lines = novo_texto.split("\n")

        largura_texto = max(fm.horizontalAdvance(l) for l in lines)
        
        if len(lines) == 1:
            altura_texto = fm.tightBoundingRect(lines[0]).height()
        else:
            altura_texto = len(lines) * fm.lineSpacing()

        mt = int(self.text_label.base_font_size * 0.07)
        mb = int(self.text_label.base_font_size * 0.04)
        ml = int(self.text_label.base_font_size * 0.04)
        mr = int(self.text_label.base_font_size * 0.04)

        new_base = QSize(
            largura_texto + ml + mr,
            altura_texto + mt + mb
        )

        mudou_tamanho = (new_base != self._base_text_size)

        self._base_text_size = new_base
        self.setMinimumSize(new_base)

        new_w = int(new_base.width() * sx)
        new_h = int(new_base.height() * sy)
        self.resize(new_w, new_h)

        log_debug_etapas(
            texto=novo_texto,
            tem_quebra="\n" in novo_texto,
            largura=largura_texto,
            altura=altura_texto,
            largura_final=new_base.width(),
            altura_final=new_base.height(),
            mudou_tamanho=mudou_tamanho
        )

        self.text_label.setScales(sx, sy)
        self._last_text = novo_texto
        log_troca_texto(novo_texto)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._press_pos = event.globalPos()
            self._resize_direction = self._get_resize_direction(event.pos())
            if not self._resize_direction:
                self._moving = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            was_resize = bool(self._resize_direction)
            self._pressed = False
            self._moving = False
            self._resize_direction = []
            if was_resize:
                log_redimensionamento(self.size(), origem="manual")

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if not self._pressed:
            self.setCursor(self._cursor_for_position(pos))
        else:
            if self._resize_direction:
                self._resize_window(event.globalPos())
            elif self._moving:
                self._move_window(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def _get_resize_direction(self, pos):
        rect = self.rect()
        m = self.MARGIN
        dirs = []
        if pos.y() <= m: dirs.append('top')
        elif pos.y() >= rect.height() - m: dirs.append('bottom')
        if pos.x() <= m: dirs.append('left')
        elif pos.x() >= rect.width() - m: dirs.append('right')
        return dirs

    def _cursor_for_position(self, pos):
        d = self._get_resize_direction(pos)
        if 'top' in d and 'left' in d:   return Qt.SizeFDiagCursor
        if 'top' in d and 'right' in d:  return Qt.SizeBDiagCursor
        if 'bottom' in d and 'left' in d:return Qt.SizeBDiagCursor
        if 'bottom' in d and 'right' in d:return Qt.SizeFDiagCursor
        if 'top' in d or 'bottom' in d:  return Qt.SizeVerCursor
        if 'left' in d or 'right' in d:  return Qt.SizeHorCursor
        return Qt.ArrowCursor

    def _resize_window(self, global_pos):
        delta = global_pos - self._press_pos
        geo = self.geometry()
        new_geo = QRect(geo)
        if 'right' in self._resize_direction:
            new_geo.setWidth(max(self.minimumWidth(), min(self.maximumWidth(), geo.width() + delta.x())))
        if 'bottom' in self._resize_direction:
            new_geo.setHeight(max(self.minimumHeight(), min(self.maximumHeight(), geo.height() + delta.y())))
        if 'left' in self._resize_direction:
            new_left = geo.left() + delta.x()
            new_w = geo.right() - new_left
            if self.minimumWidth() <= new_w <= self.maximumWidth():
                new_geo.setLeft(new_left)
        if 'top' in self._resize_direction:
            new_top = geo.top() + delta.y()
            new_h = geo.bottom() - new_top
            if self.minimumHeight() <= new_h <= self.maximumHeight():
                new_geo.setTop(new_top)
        self.setGeometry(new_geo)
        self._press_pos = global_pos

    def _move_window(self, global_pos):
        delta = global_pos - self._press_pos
        new_pos = self.pos() + delta
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        sg = screen.availableGeometry()
        w, h = self.frameGeometry().width(), self.frameGeometry().height()
        max_ov_x, max_ov_y = w//3, h//3
        min_x = sg.left() - max_ov_x
        min_y = sg.top() - max_ov_y
        max_x = sg.right() - w + max_ov_x
        max_y = sg.bottom() - h + max_ov_y
        x = max(min_x, min(new_pos.x(), max_x))
        y = max(min_y, min(new_pos.y(), max_y))
        self.move(x, y)
        self._press_pos = global_pos

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        trocar_texto_action = QAction("Trocar texto", self)
        config_action = QAction("Configurações", self)

        trocar_texto_action.triggered.connect(self.trocar_texto)
        config_action.triggered.connect(self.abrir_configuracoes)

        menu.addAction(trocar_texto_action)
        menu.addSeparator()
        menu.addAction(config_action)

        menu.exec_(event.globalPos())

    def trocar_texto(self):
        novo_texto, ok = QInputDialog.getText(self, "Trocar Texto", "Digite o novo texto:")
        if ok and novo_texto.strip():
            texto_quebrado = quebrar_texto_longo(novo_texto, max_chars_sem_espaco=20)
            self.update_text_preserving_scale(texto_quebrado)

    def abrir_configuracoes(self):
        QMessageBox.information(self, "Configurações", "Configurações ainda não implementadas.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FramelessResizableWindow()
    window.show()
    sys.exit(app.exec_())