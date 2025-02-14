import cv2
import numpy as np
import math
from inference import get_model
import supervision as sv
from deep_sort_realtime.deepsort_tracker import DeepSort


# Load video and model
video_file = "/Users/alferix/Documents/carrom/videos/vid4.mp4"
video_capture = cv2.VideoCapture(video_file)
model = get_model(model_id="carroms/1")
bounding_box_annotator = sv.BoxAnnotator()
fps = video_capture.get(cv2.CAP_PROP_FPS)

corners = []
selection_done = False

playback_speed = 1
frame_delay = int(1000 // fps)
tracker = DeepSort(max_age=120, n_init=3, nn_budget=100)  # Adjusted for 120 FPS


# Kalman Filter setup for object prediction
class KalmanTracker:
    def __init__(self, initial_position):
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array([[1, 0, 0, 0],
                                                  [0, 1, 0, 0]], np.float32)
        self.kalman.transitionMatrix = np.array([[1, 0, 1, 0],
                                                 [0, 1, 0, 1],
                                                 [0, 0, 1, 0],
                                                 [0, 0, 0, 1]], np.float32)
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)

        self.kalman.statePre = np.array([[initial_position[0]], 
                                         [initial_position[1]], 
                                         [0], [0]], np.float32)

    def predict(self):
        return self.kalman.predict()

    def correct(self, position):
        self.kalman.correct(np.array([[position[0]], [position[1]]], np.float32))


# Function to select corners of the carrom board
def select_corners(event, x, y, flags, param):
    global corners, selection_done
    if event == cv2.EVENT_LBUTTONDOWN and not selection_done:
        if len(corners) < 4:
            corners.append((x, y))
        if len(corners) == 4:
            selection_done = True


# Function to draw lines between the selected corners
def draw_board_lines(frame, corners):
    for i in range(4):
        cv2.circle(frame, corners[i], 5, (255, 0, 0), -1)
        cv2.line(frame, corners[i], corners[(i + 1) % 4], (255, 0, 0), 2)


# Function to apply perspective transform to get a top-down view of the board
def get_top_view(frame, corners):
    width = int(max(np.linalg.norm(np.array(corners[0]) - np.array(corners[1])),
                    np.linalg.norm(np.array(corners[2]) - np.array(corners[3]))))
    height = int(max(np.linalg.norm(np.array(corners[0]) - np.array(corners[3])),
                     np.linalg.norm(np.array(corners[1]) - np.array(corners[2]))))
    destination_corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype="float32")
    transformation_matrix = cv2.getPerspectiveTransform(np.array(corners, dtype="float32"), destination_corners)
    warped_frame = cv2.warpPerspective(frame, transformation_matrix, (width, height))
    return warped_frame


# Calculate Euclidean distance between two points
def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# Object tracking dictionary
coin_tracks = {}
frame_interval = 40  # Number of frames to calculate velocity over

# Function to track and calculate velocity of detected objects (coins)
def track_and_calculate_velocity(frame, detections, frame_id):
    global coin_tracks

    detection_centroids = []

    # Get frame dimensions for thresholds
    frame_height, frame_width = frame.shape[:2]
    noise_tolerance = 2  # Pixels considered as noise

    # Prepare detection boxes for Deep SORT
    detection_boxes = []
    detection_confidences = []

    for detection in detections:
        bbox = detection[0]  # Extract bounding box coordinates
        x1, y1, x2, y2 = map(int, bbox)
        confidence = detection[1]  # Confidence score of the detection
        detection_boxes.append([x1, y1, x2, y2])
        detection_confidences.append(confidence)

    # Update the Deep SORT tracker with detections
    tracks = tracker.update_tracks(detection_boxes, detection_confidences, frame=frame)

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        bbox = track.to_tlbr()  # Get the tracked bounding box [x1, y1, x2, y2]

        # Calculate object center using bounding box
        object_center = np.array([(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2])

        # If this is a new object, initialize tracking information
        if track_id not in coin_tracks:
            coin_tracks[track_id] = {'centroid': object_center, 'positions': {frame_id: object_center}, 'velocity': 0, 'last_update': frame_id}
        else:
            # Update object information
            coin_tracks[track_id]['centroid'] = object_center
            coin_tracks[track_id]['last_update'] = frame_id

            # Store position for this frame
            coin_tracks[track_id]['positions'][frame_id] = object_center

            # Remove older frame positions (older than 20 frames ago)
            oldest_frame = frame_id - frame_interval
            if oldest_frame in coin_tracks[track_id]['positions']:
                del coin_tracks[track_id]['positions'][oldest_frame]

            # Calculate velocity every 20 frames
            if frame_id % frame_interval == 0 and oldest_frame in coin_tracks[track_id]['positions']:
                previous_position = coin_tracks[track_id]['positions'][oldest_frame]
                distance = calculate_distance(previous_position, object_center)

                # Update velocity if the movement exceeds noise tolerance
                if distance > noise_tolerance:
                    time_elapsed = frame_interval / fps  # Time elapsed over 20 frames
                    velocity = distance / time_elapsed  # Pixels per second
                    coin_tracks[track_id]['velocity'] = velocity
                else:
                    coin_tracks[track_id]['velocity'] = 0

        # Draw ID and velocity on the frame
        cv2.circle(frame, tuple(object_center), 5, (0, 255, 0), -1)
        cv2.putText(frame, f'ID:{track_id} V:{coin_tracks[track_id]["velocity"]:.2f}px/s',
                    (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


# Set up window and mouse callback
cv2.namedWindow("Annotated Video")
cv2.setMouseCallback("Annotated Video", select_corners)

# Main loop for processing the video
frame_id = 0
while video_capture.isOpened():
    ret, frame = video_capture.read()
    if not ret:
        break

    # Once four corners are selected, apply perspective transform
    if selection_done:
        top_view_frame = get_top_view(frame, corners)

        # Run inference on top-down view
        results = model.infer(top_view_frame)[0]
        detections = sv.Detections.from_inference(results)

        # Annotate frame and track coins
        annotated_frame = bounding_box_annotator.annotate(scene=top_view_frame, detections=detections)
        track_and_calculate_velocity(annotated_frame, detections, frame_id)

        # Display FPS on frame
        cv2.putText(annotated_frame, f"FPS: {int(fps / playback_speed)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # Show annotated frame
        cv2.imshow("Annotated Video", annotated_frame)
    
    else:
        # Show frame with corner selection prompt if corners are not yet selected
        cv2.putText(frame, "Select 4 corners of the carrom board", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        for corner in corners:
            cv2.circle(frame, corner, 5, (0, 0, 255), -1)
        cv2.imshow("Annotated Video", frame)
