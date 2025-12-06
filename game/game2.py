import random
import time
from tkinter import messagebox
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance as dist
from util import calculate_score

def run_game2_engine(buzzer, cap, face_mesh, num_rounds, screen_w, screen_h):
    all_r_times = []
    all_scores = []

    if not cap or not cap.isOpened():
        # messagebox is not thread-safe, so we just print and return
        print("Error: Camera Not Found or not opened.")
        return all_r_times, all_scores

    if buzzer:
        try:
            buzzer.write(1)
        except Exception as e:
            print(f"Buzzer write failed: {e}")

    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    def calculate_ear(eye_points, landmarks):
        A = dist.euclidean(landmarks[eye_points[1]], landmarks[eye_points[5]])
        B = dist.euclidean(landmarks[eye_points[2]], landmarks[eye_points[4]])
        C = dist.euclidean(landmarks[eye_points[0]], landmarks[eye_points[3]])
        ear = (A + B) / (2.0 * C)
        return ear

    window_name = 'Blink Game'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    win_w, win_h = 800, 600
    pos_x = (screen_w - win_w) // 2
    pos_y = (screen_h - win_h) // 2
    cv2.resizeWindow(window_name, win_w, win_h)
    cv2.moveWindow(window_name, pos_x, pos_y)

    try:
        for current_round in range(1, num_rounds + 1):
            # --- Show Round Start Screen ---
            blank_frame = np.zeros((win_h, win_w, 3), dtype=np.uint8)
            round_text = f"ROUND {current_round}/{num_rounds}"
            ready_text = "READY..."
            round_text_size = cv2.getTextSize(round_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            ready_text_size = cv2.getTextSize(ready_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
            round_text_x = (win_w - round_text_size[0]) // 2
            round_text_y = (win_h // 2) - 50
            ready_text_x = (win_w - ready_text_size[0]) // 2
            ready_text_y = (win_h // 2) + 50
            draw_text_with_outline(blank_frame, round_text, (round_text_x, round_text_y), 1.0, 2)
            draw_text_with_outline(blank_frame, ready_text, (ready_text_x, ready_text_y), 1.5, 3, text_color=(0, 255, 255))
            cv2.imshow(window_name, blank_frame)
            if cv2.waitKey(random.randint(1500, 3000)) == 27:
                raise InterruptedError("Game exited during ready screen")

            # --- Start Single Round Logic ---
            game_state = "WAITING"
            start_time = 0
            beep_start_time = 0
            random_wait = random.uniform(2, 5)
            wait_start = time.time()
            round_reaction = None
            round_score = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    raise IOError("Failed to read frame from camera")

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
                center_x, center_y = w // 2, h // 2

                if game_state == "WAITING":
                    draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)
                    if time.time() - wait_start > random_wait:
                        if buzzer: buzzer.write(0)
                        start_time = time.time()
                        beep_start_time = time.time()
                        game_state = "BEEPING"
                elif game_state == "BEEPING":
                    draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)
                    if time.time() - beep_start_time > 0.1:
                        if buzzer: buzzer.write(1)
                        game_state = "MEASURING"
                elif game_state == "MEASURING":
                    draw_text_with_outline(frame, "BLINK NOW!", (center_x - 150, center_y), 2.0, 4, text_color=(0, 0, 255))
                    if 0.0 < current_ear < 0.22:
                        end_time = time.time()
                        reaction_sec = end_time - start_time
                        if buzzer: buzzer.write(1)
                        round_score = calculate_score(reaction_sec)
                        round_reaction = reaction_sec
                        break  # End of round

                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) == 27:
                    raise InterruptedError("Game exited by user")

            # --- Show Round Result ---
            all_r_times.append(round_reaction)
            all_scores.append(round_score)
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                feedback_line = f"{round_reaction * 1000:.1f} ms" if round_reaction is not None else "FAIL"
                score_line = f"Score: {round_score} pts"
                font = cv2.FONT_HERSHEY_SIMPLEX
                scale1, scale2, thickness = 1.0, 1.5, 2
                s2_w, s2_h = cv2.getTextSize(feedback_line, font, scale2, thickness)[0]
                s3_w, s3_h = cv2.getTextSize(score_line, font, scale1, thickness)[0]
                padding_x, padding_y = 20, 20
                draw_text_with_outline(frame, feedback_line, (w - s2_w - padding_x, h - s3_h - padding_y - 5), scale2, thickness, text_color=(0, 255, 255))
                draw_text_with_outline(frame, score_line, (w - s3_w - padding_x, h - padding_y), scale1, thickness, text_color=(255, 255, 255))
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1500) == 27:
                     raise InterruptedError("Game exited during feedback")

    except (InterruptedError, IOError) as e:
        print(f"Game 2 interrupted or failed: {e}")
        # Fill remaining rounds with failed results
        remaining_rounds = num_rounds - len(all_r_times)
        for _ in range(remaining_rounds):
            all_r_times.append(None)
            all_scores.append(0)
    finally:
        if buzzer:
            try:
                buzzer.write(1)
            except: pass
        cv2.destroyAllWindows()
        for i in range(10): cv2.waitKey(1)

    return all_r_times, all_scores


def draw_text_with_outline(img, text, pos, font_scale, font_thickness, text_color=(255, 255, 255),
                           outline_color=(0, 0, 0)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, outline_color, font_thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness, cv2.LINE_AA)
