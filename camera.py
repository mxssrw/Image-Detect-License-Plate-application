import cv2
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from ultralytics import YOLO
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import pytesseract
from fuzzywuzzy import process
from collections import defaultdict, Counter
from cv2 import dnn_superres
import time
from utils.provinces import province_list

class CameraWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)# ให้กล้องเต็มพื้นที่ตาม layout
        self.setMinimumSize(640, 480)
        self.setScaledContents(True)  # fit ภาพตาม QLabel

        # ตั้งเวลาสำหรับการอัปเดตภาพ
        self.timer = QTimer() 
        self.timer.setInterval(0) 
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(0)

        self.on_frame_processed = None
        self.on_text_detected = None

    def update_frame(self):
        model = YOLO('/mnt/g/Image processing/best.pt')
        model_CD = YOLO('/mnt/g/Image processing/best_char_detector.pt')
        font = ImageFont.truetype('/mnt/g/Image processing/THSarabunNew.ttf', 64)
        font_color = (255, 0, 0)
        sr = dnn_superres.DnnSuperResImpl_create()
        sr.readModel('/mnt/g/Image processing/FSRCNN_x4.pb')
        sr.setModel('fsrcnn', 4)

        video_path = '/mnt/g/Image processing/VID_20250520_172109.mp4'
        cap = cv2.VideoCapture(video_path)
        output_path = '/mnt/g/Image processing/result/output_tracked.avi'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

        frame_idx = 0
        plate_results_cache = {}
        first_seen_time = {}
        delay_sec = 3
        plate_buffer = defaultdict(list)
        province_buffer = defaultdict(list)

        def preprocess_plate(img):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        def is_sharp(image):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            return laplacian.var()

        def get_closest_province(texts, choices):
            all_matches = [process.extractOne(t, choices)[0] for t in texts if t.strip()]
            return Counter(all_matches).most_common(1)[0][0] if all_matches else ""
    
        ret, frame = self.cap.read()
        if not ret:
            return

        result = model.track(frame, persist=True, tracker="botsort.yaml", conf=0.3)[0]
        draw_frame = Image.fromarray(cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB))
        draw_main = ImageDraw.Draw(draw_frame)

        if result.boxes and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy().astype(int)
            track_ids = result.boxes.id.int().cpu().tolist()

            for (x1, y1, x2, y2), track_id in zip(boxes, track_ids):
                if track_id not in first_seen_time:
                    first_seen_time[track_id] = time.time()

                plate_img = frame[y1:y2, x1:x2]
                plate_processed = preprocess_plate(plate_img)
                plate_upscaled = sr.upsample(plate_processed)

                if (time.time() - first_seen_time[track_id]) < delay_sec:
                    plate_buffer[track_id].append(plate_upscaled)
                    continue

                if track_id not in plate_results_cache:
                    buffer_imgs = plate_buffer[track_id][-5:]
                    if not buffer_imgs:
                        continue
                    sharpest_plate = max(buffer_imgs, key=is_sharp) # Get the sharpest image for store frame in on_frame_processed

                    results_cd = model_CD.predict(sharpest_plate, conf=0.3, verbose=False)
                    license_plate_boxes = []
                    province_votes = []

                    for rc in results_cd:
                        for b in rc.boxes:
                            cx1, cy1, cx2, cy2 = map(int, b.xyxy[0])
                            cls = int(b.cls[0])
                            label = model_CD.names[cls]

                            if label.lower() == "province":
                                crop = sharpest_plate[cy1:cy2, cx1:cx2]
                                province_text = pytesseract.image_to_string(crop, config='--psm 6 -l tha')
                                province_votes.append(province_text)
                            else:
                                license_plate_boxes.append((cx1, label))

                    license_plate_boxes.sort(key=lambda x: x[0])
                    license_text = ''.join([l for _, l in license_plate_boxes])
                    final_province = get_closest_province(province_votes, province_list)

                    plate_results_cache[track_id] = {
                        "license": license_text,
                        "province": final_province
                    }

                cached_result = plate_results_cache.get(track_id, {})
                display_text = f"ID {track_id} | {cached_result.get('license', '')} | {cached_result.get('province', '')}"
                draw_main.rectangle([(x1, y1), (x2, y2)], outline="green", width=3)
                draw_main.text((x1, max(0, y1 - 40)), display_text, font=font, fill=font_color)

        final_frame = cv2.cvtColor(np.array(draw_frame), cv2.COLOR_RGB2BGR)
        out.write(final_frame)
        frame_idx += 1

        # เลิือก sharpest_plate, display_text ไปโชว์ใน info panel 
        if self.on_frame_processed:
            self.on_frame_processed(sharpest_plate, display_text)

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(qt_image))

        