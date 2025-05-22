from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import cv2

class InfoPanel(QWidget):
    def __init__(self):
        super().__init__()

        # Layout สำหรับรายการใบหน้า
        self.content_layout = QVBoxLayout()

        # Widget ที่จะอยู่ภายใน Scroll Area
        scroll_content = QWidget()
        scroll_content.setLayout(self.content_layout)

        # Scroll Area ที่บรรจุ scroll_content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)

        # Layout หลักของ InfoPanel
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def add_face_info(self, image, text):
        # Convert image to QPixmap
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image).scaled(100, 100, Qt.KeepAspectRatio)

        # Create row widget
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_widget.setLayout(row_layout)

        img_label = QLabel()
        img_label.setPixmap(pixmap)
        img_label.setFixedSize(pixmap.size())
        img_label.setScaledContents(False)

        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #333;
                padding: 4px;
                background-color: #f0f0f0;
                border-radius: 6px;
            }
        """)

        row_layout.addWidget(img_label)
        row_layout.addWidget(text_label)
        row_layout.setAlignment(Qt.AlignVCenter)

        self.content_layout.addWidget(row_widget)