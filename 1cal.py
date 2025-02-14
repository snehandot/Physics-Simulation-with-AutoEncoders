import cv2
import numpy as np
import math
from inference import get_model
import supervision as sv

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
next_id = 0
frame_id = 0

# Function to track and calculate velocity of detected objects (coins)
frame_interval = 20  # Number of frames to calculate velocity over
stall_velocity_threshold = 1  # Threshold below which an object is considered stalled

frame_interval = 20  # Number of frames to calculate velocity over

def track_and_calculate_velocity(frame, detections, frame_id):
    global coin_tracks, next_id

    detection_centroids = []

    # Get frame dimensions for thresholds
    frame_height, frame_width = frame.shape[:2]
    diagonal_threshold = np.sqrt(frame_width**2 + frame_height**2) / 50  # Significant movement threshold
    noise_tolerance = 2  # Pixels considered as noise

    # Threshold for object disappearance (5 seconds)
    max_disappear_frames = 5 * fps

    # Remove objects that haven't reappeared in 5 seconds
    to_remove = []
    for coin_id, data in coin_tracks.items():
        if frame_id - data['frame_id'] > max_disappear_frames:
            to_remove.append(coin_id)

    for coin_id in to_remove:
        del coin_tracks[coin_id]

    for i, detection in enumerate(detections):
        bbox = detection[0]
        x1, y1, x2, y2 = map(int, bbox)

        # Calculate object center using bounding box
        object_center = np.array([(x1 + x2) // 2, (y1 + y2) // 2])
        detection_centroids.append(object_center)

        # Find best match from existing tracked objects
        best_match_id = None
        best_match_distance = float('inf')

        for coin_id, data in coin_tracks.items():
            last_position = data['centroid']
            distance = calculate_distance(last_position, object_center)

            if distance < best_match_distance and distance < diagonal_threshold:
                best_match_distance = distance
                best_match_id = coin_id

        if best_match_id is None:
            # No match found, assign a new ID
            best_match_id = next_id
            next_id += 1
            coin_tracks[best_match_id] = {'centroid': object_center, 'kalman': KalmanTracker(object_center), 
                                          'frame_id': frame_id, 'positions': {frame_id: object_center}, 'velocity': 0}
        
        # Update Kalman filter and object tracking
        coin_tracks[best_match_id]['kalman'].correct(object_center)
        coin_tracks[best_match_id]['centroid'] = object_center
        coin_tracks[best_match_id]['frame_id'] = frame_id

        # Store position for this frame
        coin_tracks[best_match_id]['positions'][frame_id] = object_center

        # Remove older frame positions (older than 20 frames ago)
        oldest_frame = frame_id - frame_interval
        if oldest_frame in coin_tracks[best_match_id]['positions']:
            del coin_tracks[best_match_id]['positions'][oldest_frame]

        # Calculate velocity every 20 frames
        if frame_id % frame_interval == 0 and oldest_frame in coin_tracks[best_match_id]['positions']:
            previous_position = coin_tracks[best_match_id]['positions'][oldest_frame]
            distance = calculate_distance(previous_position, object_center)
            
            # Update velocity if the movement exceeds noise tolerance
            if distance > noise_tolerance:
                time_elapsed = frame_interval / fps  # Time elapsed over 20 frames
                velocity = distance / time_elapsed  # Pixels per second
                coin_tracks[best_match_id]['velocity'] = velocity
            else:
                coin_tracks[best_match_id]['velocity'] = 0

        # Draw ID and velocity on the frame
        cv2.circle(frame, tuple(object_center), 5, (0, 255, 0), -1)
        cv2.putText(frame, f'ID:{best_match_id} V:{coin_tracks[best_match_id]["velocity"]:.2f}px/s',
                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Set up window and mouse callback
cv2.namedWindow("Annotated Video")
cv2.setMouseCallback("Annotated Video", select_corners)

# Main loop for processing the video
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

    # Handle keypresses for playback speed control
    key = cv2.waitKey(frame_delay)
    if key & 0xFF == ord('q'):  # Quit video
        break
    elif key == ord('+'):  # Increase playback speed
        playback_speed = max(0.1, playback_speed - 0.1)
        frame_delay = int(1000 // (fps / playback_speed))
    elif key == ord('-'):  # Decrease playback speed
        playback_speed = min(2.0, playback_speed + 0.1)
        frame_delay = int(1000 // (fps / playback_speed))

    frame_id += 1

# Release video capture and close windows
video_capture.release()
cv2.destroyAllWindows()
