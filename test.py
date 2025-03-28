from flask import Flask, Response
import cv2
import requests
import numpy as np

app = Flask(__name__)
STREAM_URL = 'http://192.168.77.1:8080/?action=stream'

# Загрузка модели YOLOv4-tiny
net = cv2.dnn.readNet("yolo_model/yolov4-tiny.weights",
                     "yolo_model/yolov4-tiny.cfg")
classes = []
with open("yolo_model/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers().flatten()]


def detect_objects(frame):
    height, width, channels = frame.shape

    # Подготовка изображения для нейросети
    blob = cv2.dnn.blobFromImage(
        frame, 0.00392, (416, 416), (0, 0, 0),
        True, crop=False
    )

    # Прямой проход через сеть
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Анализ результатов
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # Порог уверенности
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Координаты прямоугольника
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Подавление немаксимумов
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Отрисовка результатов
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = f"{classes[class_ids[i]]} {confidences[i]:.2f}"
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    return frame


def generate_frames():
    stream = requests.get(STREAM_URL, stream=True)
    bytes_buffer = bytes()

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_buffer += chunk
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg_data = bytes_buffer[a:b + 2]
            bytes_buffer = bytes_buffer[b + 2:]

            frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

            # Добавление детекции объектов
            frame = detect_objects(frame)

            # Красная линия
            height, width = frame.shape[:2]
            line_y = int(height * 0.8)
            cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return """
    <html>
      <head>
        <title>Object Detection</title>
      </head>
      <body>
        <h1>Real-time Object Detection</h1>
        <img src="/video_feed" style="width: 640px; height: 480px;">
      </body>
    </html>
    """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)