import cv2
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer


class CameraWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

        # ให้กล้องเต็มพื้นที่ตาม layout
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 480)
        self.setScaledContents(True)  # fit ภาพตาม QLabel

        self.timer = QTimer() 
        self.timer.setInterval(0) # ตั้งเวลาให้ timer เริ่มทำงานทุกๆ 30 ms
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(0)

        self.on_frame_processed = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        if self.on_frame_processed:
            self.on_frame_processed(frame)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qt_image))