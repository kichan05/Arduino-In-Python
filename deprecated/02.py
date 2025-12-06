import cv2
import time
import random
import pyfirmata2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from scipy.spatial import distance as dist

try:
    PORT = pyfirmata2.Arduino.AUTODETECT
    board = pyfirmata2.Arduino(PORT)
    print("아두이노 연결 성공")

    it = pyfirmata2.util.Iterator(board)
    it.start()

    buzzer = board.get_pin('d:3:o')

    buzzer.write(1)

    time.sleep(3)

except Exception as e:
    print("ERROR")
    exit()

# AI (MediaPipe) 설정
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def calculate_ear(eye_points, landmarks):
    A = dist.euclidean(landmarks[eye_points[1]], landmarks[eye_points[5]])
    B = dist.euclidean(landmarks[eye_points[2]], landmarks[eye_points[4]])
    C = dist.euclidean(landmarks[eye_points[0]], landmarks[eye_points[3]])
    ear = (A + B) / (2.0 * C)
    return ear


# 게임
cap = cv2.VideoCapture(0)
print("s키 : 게임 시작")
print("ESC 키 : 프로그램 종료")

game_state = "IDLE"
start_time = 0
beep_start_time = 0
random_wait = 0
wait_start = 0

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    h, w, _ = frame.shape

    current_ear = 0

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        mesh_points = [(int(pt.x * w), int(pt.y * h)) for pt in landmarks]

        left_ear = calculate_ear(LEFT_EYE, mesh_points)
        right_ear = calculate_ear(RIGHT_EYE, mesh_points)
        current_ear = (left_ear + right_ear) / 2.0

        cv2.putText(frame, f"EAR: {current_ear:.2f}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=results.multi_face_landmarks[0],
            connections=mp_face_mesh.FACEMESH_IRISES,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style()
        )
        mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=results.multi_face_landmarks[0],
            connections=mp_face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_contours_style()
        )

    # 게임 로직
    if game_state == "WAITING":
        if time.time() - wait_start > random_wait:
            buzzer.write(0)

            start_time = time.time()
            beep_start_time = time.time()
            game_state = "BEEPING"

    elif game_state == "BEEPING":
        if time.time() - beep_start_time > 0.1:
            buzzer.write(1)
            game_state = "MEASURING"

    elif game_state == "MEASURING":
        # 반응 감지
        if current_ear < 0.22 and current_ear > 0.0:
            end_time = time.time()

            reaction_ms = (end_time - start_time) * 1000

            buzzer.write(1)

            print(f"기록: {reaction_ms:.1f}ms")

            cv2.putText(frame, f"{reaction_ms:.1f}ms", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

            cv2.imshow('Reaction Game', frame)

            cv2.waitKey(3000)
            game_state = "IDLE"
            print("재시작 : s키")

    cv2.imshow('Reaction Game', frame)

    key = cv2.waitKey(1)
    if key == 27:
        break
    elif key == ord('s') and game_state == "IDLE":
        print("⏳ 준비... (랜덤 대기)")
        buzzer.write(1)
        game_state = "WAITING"
        wait_start = time.time()
        random_wait = random.uniform(2, 5)

# 종료
try:
    buzzer.write(1)
    board.exit()
except:
    pass
cap.release()
cv2.destroyAllWindows()
