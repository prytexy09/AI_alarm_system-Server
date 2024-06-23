import cv2
from ultralytics import YOLO
import asyncio
import websockets
import time
import threading
from threading import Lock
import cv2

class Camera:
    last_frame = None
    last_ready = None
    lock = Lock()

    def __init__(self, rtsp_link):
        capture = cv2.VideoCapture(rtsp_link)
        thread = threading.Thread(target=self.rtsp_cam_buffer, args=(capture,), name="rtsp_read_thread")
        thread.daemon = True
        thread.start()

    def rtsp_cam_buffer(self, capture):
        while True:
            with self.lock:
                self.last_ready, self.last_frame = capture.read()


    def getFrame(self):
        if (self.last_ready is not None) and (self.last_frame is not None):
            return self.last_frame.copy()
        else:
            return None

# Путь к RTSP потоку
rtsp_url = "rtsp://admin:1XSCXW%@192.168.27.77"

# Загрузка модели YOLOv8
model = YOLO("yolov8n.pt")  # Используем предобученную модель YOLOv8n

# URL WebSocket сервера
websocket_url = "ws://localhost:8760"

# Функция для изменения размера кадра
def resize_frame(frame, width):
    height = int(frame.shape[0] * width / frame.shape[1])
    resized_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
    return resized_frame

# Функция для вызова тревоги
async def alarm():
    async with websockets.connect(websocket_url) as websocket:
        await websocket.send("alarm")
        print("Тревога! Обнаружен человек на нескольких кадрах подряд!")

# Функция для детекции объектов на кадре и визуализации результатов
def process_frame(frame):
    results = model(frame)
    
    # Извлечение названий и вероятностей всех найденных объектов
    detected_objects = []
    for result in results:
        for class_id, confidence in zip(result.boxes.cls, result.boxes.conf):
            class_id = int(class_id)  # Преобразование в int для корректного доступа к именам классов
            confidence = float(confidence)  # Преобразование в float для удобства
            if class_id in result.names:
                detected_objects.append((result.names[class_id], confidence))
            else:
                detected_objects.append((f"Unknown class ID {class_id}", confidence))

    # Визуализация результатов
    annotated_frame = results[0].plot()  # Рисуем результаты на кадре
    annotated_frame = resize_frame(annotated_frame, 1200)
    
    return annotated_frame, detected_objects

# Основной код для захвата и обработки видео потока
async def main():
    cap = Camera(rtsp_url)
    
    cadr = 0
    if False:
        print("Не удается открыть RTSP поток")
        return
    else:
        person_count = 0  # Счетчик кадров с обнаружением человека
        
        while True:
            #time.sleep(0.5)
            cadr += 1


            frame = cap.getFrame()
            # if not ret:
            #     print("Не удается захватить кадр")
            #     break
            
            
            annotated_frame, detected_objects = process_frame(frame)
            
            # Вывод названий всех найденных объектов с вероятностями
            print("Найденные объекты:", detected_objects)
            
            # Проверка на наличие человека (person)
            person_detected = any(obj[0] == "person" for obj in detected_objects)
            if person_detected:
                person_count += 1
            else:
                person_count = 0
            
            # Вызов тревоги, если человек обнаружен на более чем 5 кадрах подряд
            if person_count > 5:
                await alarm()
                person_count = 0  # Сброс счетчика после вызова тревоги
            
            # Показать изображение с аннотациями
            cv2.imshow("YOLOv8 Detection", annotated_frame)
            
            # Ожидание клавиши 'q' для выхода из цикла
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

# Запуск основного кода
asyncio.run(main())
