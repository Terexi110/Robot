from flask import Flask, Response
import cv2
import requests
import numpy as np

app = Flask(__name__)
STREAM_URL = 'http://192.168.184.173:8080/?action=stream'


def generate_frames():
    # Подключаемся к исходному стриму
    stream = requests.get(STREAM_URL, stream=True)
    bytes_buffer = bytes()

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_buffer += chunk
        a = bytes_buffer.find(b'\xff\xd8')  # Начало JPEG
        b = bytes_buffer.find(b'\xff\xd9')  # Конец JPEG

        if a != -1 and b != -1:
            jpg_data = bytes_buffer[a:b + 2]
            bytes_buffer = bytes_buffer[b + 2:]

            # Декодируем кадр
            frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)

            # Добавляем красную линию (20% от верхнего края)
            height, width = frame.shape[:2]
            line_y = int(height * 0.8)
            cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

            # Кодируем обратно в JPEG
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
        <title>Video Stream</title>
      </head>
      <body>
        <h1>Modified Video Stream</h1>
        <img src="/video_feed" style="width: 640px; height: 480px;">
      </body>
    </html>
    """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)