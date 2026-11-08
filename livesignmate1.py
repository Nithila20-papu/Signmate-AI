
import cv2
import mediapipe as mp
import os
import time
import joblib
import numpy as np
import pandas as pd

from collections import deque
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class SignMateRecognizer:

    def __init__(self):

        project_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        model_path = os.path.join(
            project_folder,
            "sign_language_model_normalized.pkl"
        )

        mediapipe_path = os.path.join(
            project_folder,
            "hand_landmarker.task"
        )

        model_data = joblib.load(model_path)

        self.model = model_data["model"]
        self.feature_columns = model_data["feature_columns"]

        base_options = python.BaseOptions(
            model_asset_path=mediapipe_path
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2
        )

        self.detector = vision.HandLandmarker.create_from_options(
            options
        )

        self.sequence_length = 20
        self.sequence = deque(maxlen=20)

        self.state = "READY"
        self.predicted_letter = ""
        self.confidence = 0.0

        self.countdown_start = 0
        self.last_sample_time = 0

        self.sample_interval = 0.15
        self.countdown_seconds = 3

        print("SignMate AI model loaded!")

    def normalize_hand(self, hand_points):

        points = np.array(
            hand_points, dtype=float
        ).reshape(21, 3)

        if np.allclose(points, 0.0):
            return points.flatten().tolist()

        wrist = points[0].copy()
        points = points - wrist

        distances = np.sqrt(
            points[:, 0] ** 2 +
            points[:, 1] ** 2
        )

        scale = np.max(distances)

        if scale < 1e-8:
            return np.zeros(63).tolist()

        points = points / scale

        return points.flatten().tolist()

    def get_frame_features(self, hands):

        features = []

        if hands:

            sorted_hands = sorted(
                hands,
                key=lambda hand: hand[0].x
            )

            for hand in sorted_hands[:2]:

                raw_features = []

                for landmark in hand:
                    raw_features.extend([
                        landmark.x,
                        landmark.y,
                        landmark.z
                    ])

                features.extend(
                    self.normalize_hand(raw_features)
                )

        while len(features) < 126:
            features.extend([0.0] * 63)

        return features

    def start_prediction(self):

        self.sequence.clear()

        self.predicted_letter = ""
        self.confidence = 0.0

        self.state = "WAITING_HAND"

    def process_frame(self, frame):

        rgb = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        result = self.detector.detect(mp_image)

        hands = result.hand_landmarks
        hand_detected = bool(hands)

        # Draw hand landmarks

        if hand_detected:

            for hand in hands:
                for landmark in hand:

                    x = int(
                        landmark.x * frame.shape[1]
                    )

                    y = int(
                        landmark.y * frame.shape[0]
                    )

                    cv2.circle(
                        frame,
                        (x, y),
                        5,
                        (0, 255, 0),
                        -1
                    )

        # Wait for hand

        if self.state == "WAITING_HAND":

            if hand_detected:
                self.countdown_start = time.time()
                self.state = "COUNTDOWN"

        # Countdown

        if self.state == "COUNTDOWN":

            if not hand_detected:
                self.state = "WAITING_HAND"

            else:

                elapsed = (
                    time.time() - self.countdown_start
                )

                remaining = (
                    self.countdown_seconds - int(elapsed)
                )

                if elapsed >= self.countdown_seconds:

                    self.sequence.clear()
                    self.last_sample_time = 0

                    self.state = "RECORDING"

                else:

                    cv2.putText(
                        frame,
                        str(remaining),
                        (frame.shape[1] // 2 - 30,
                         frame.shape[0] // 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        3,
                        (0, 255, 255),
                        5
                    )

        # Collect 20 frames

        if self.state == "RECORDING":

            now = time.time()

            if now - self.last_sample_time >= self.sample_interval:

                features = self.get_frame_features(hands)

                self.sequence.append(features)

                self.last_sample_time = now

            if len(self.sequence) >= self.sequence_length:

                sequence_features = []

                for features in self.sequence:
                    sequence_features.extend(features)

                prediction_input = pd.DataFrame(
                    [sequence_features],
                    columns=self.feature_columns
                )

                self.predicted_letter = self.model.predict(
                    prediction_input
                )[0]

                probabilities = self.model.predict_proba(
                    prediction_input
                )[0]

                self.confidence = (
                    max(probabilities) * 100
                )

                self.state = "RESULT"

        # Display status on camera

        status = {
            "READY": "Press Start Prediction",
            "WAITING_HAND": "Show your hand",
            "COUNTDOWN": "Get ready!",
            "RECORDING": (
                f"Recording: {len(self.sequence)}/20"
            ),
            "RESULT": f"Prediction: {self.predicted_letter}"
        }

        cv2.putText(
            frame,
            "SignMate AI",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            status[self.state],
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        if self.state == "RESULT":

            cv2.putText(
                frame,
                f"Confidence: {self.confidence:.1f}%",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        return frame

    def close(self):
        self.detector.close()
