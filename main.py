from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QSizePolicy
from camera import CameraWidget
from info_panel import InfoPanel
import sys



class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera App with Face Info")
        self.setGeometry(100, 100, 1000, 600)

        # Widgets
        self.camera_widget = CameraWidget()
        self.info_panel = InfoPanel()

        self.camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.info_panel .setFixedWidth(300)

        # Connect callback
        self.camera_widget.on_frame_processed = self.process_frame

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.camera_widget, stretch=3)
        layout.addWidget(self.info_panel, stretch=1)
        self.setLayout(layout)

    # function ที่จะถูกเรียกเมื่อมีการประมวลผลเฟรมจากกล้อง
    def process_frame(self, frame, display_text):
        h, w, _ = frame.shape
        cropped_face = frame

        self.info_panel.add_face_info(cropped_face, display_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())