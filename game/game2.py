import random
import time
from tkinter import messagebox
import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
from util import calculate_score

def run_ai_blink_game(board, root):
    if board is None:
        messagebox.showerror("Error", "Arduino Not Connected")
        return None, None

    try:
        buzzer = board.get_pin('d:3:o')
        buzzer.write(1)
    except Exception as e:
        print(f"Pin Setup Failed: {e}")
        return None, None

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    def calculate_ear(eye_points, landmarks):
        A = dist.euclidean(landmarks[eye_points[1]], landmarks[eye_points[5]])
        B = dist.euclidean(landmarks[eye_points[2]], landmarks[eye_points[4]])
        C = dist.euclidean(landmarks[eye_points[0]], landmarks[eye_points[3]])
        ear = (A + B) / (2.0 * C)
        return ear

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Camera Not Found")
        return None, None

    window_name = 'Blink Game'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    win_w, win_h = 800, 600
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    pos_x = (screen_w - win_w) // 2
    pos_y = (screen_h - win_h) // 2

    cv2.resizeWindow(window_name, win_w, win_h)
    cv2.moveWindow(window_name, pos_x, pos_y)

    root.withdraw()

    game_state = "WAITING"
    start_time = 0
    beep_start_time = 0
    random_wait = random.uniform(2, 5)
    wait_start = time.time()

    final_reaction = None
    final_score = 0

    # 게임 루프
    try:
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

            center_x = w // 2
            center_y = h // 2

            # 게임 시작 시
            if game_state == "WAITING":
                draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)

                if time.time() - wait_start > random_wait:
                    buzzer.write(0)
                    start_time = time.time()
                    beep_start_time = time.time()
                    game_state = "BEEPING"

            elif game_state == "BEEPING":
                draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)
                if time.time() - beep_start_time > 0.1:
                    buzzer.write(1)
                    game_state = "MEASURING"
            # 반응속도 측정 시
            elif game_state == "MEASURING":
                draw_text_with_outline(frame, "BLINK NOW!", (center_x - 150, center_y), 2.0, 4, text_color=(0, 0, 255))

                if current_ear < 0.22 and current_ear > 0.0:
                    end_time = time.time()
                    reaction_sec = end_time - start_time
                    buzzer.write(1)

                    final_score = calculate_score(reaction_sec)
                    final_reaction = reaction_sec

                    # 결과 대기 문구 표시
                    ret, frame = cap.read()
                    frame = cv2.flip(frame, 1)

                    wait_msg = "PLEASE WAIT FOR RESULT..."

                    font_scale = 1.0
                    thickness = 2
                    text_size = cv2.getTextSize(wait_msg, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                    text_w, text_h = text_size

                    # 화면 중앙 좌표
                    text_x = (w - text_w) // 2
                    text_y = (h + text_h) // 2

                    # 대기 문구
                    draw_text_with_outline(frame, wait_msg, (text_x, text_y), font_scale, thickness,
                                           text_color=(0, 255, 255))
                    cv2.imshow(window_name, frame)
                    cv2.waitKey(1500)
                    break

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) == 27:
                final_reaction = None
                break

    finally:
        try:
            buzzer.write(1)
        except:
            pass
        cap.release()
        cv2.destroyAllWindows()
        for i in range(10): cv2.waitKey(1)

    return final_reaction, final_score


def draw_text_with_outline(img, text, pos, font_scale, font_thickness, text_color=(255, 255, 255),
                           outline_color=(0, 0, 0)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, outline_color, font_thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness, cv2.LINE_AA)
