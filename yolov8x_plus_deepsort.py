import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# Initialize the YOLO model
model = YOLO('yolov8x.pt')
model.fuse()  # Fuse layers for faster inference

# Initialize DeepSORT tracker
tracker = DeepSort(max_age=60, n_init=3, max_iou_distance=0.7)

# Set to store unique person IDs
unique_person_ids = set()

def count_and_display_people(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    frame_num = 0  # Track the frame number

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # Stop if the video ends

        # Run YOLO inference (only 'person' class with ID 0)
        results = model(frame, classes=[0])

        # Collect detections in [left, top, width, height, confidence] format
        detections = []

        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 0:  # Class ID 0 corresponds to 'person'
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = box.conf[0].item()  # Get confidence score

                    # Convert [x1, y1, x2, y2] to [left, top, width, height]
                    left, top = x1, y1
                    width, height = x2 - x1, y2 - y1

                    # Append detection in the required format
                    detections.append(([left, top, width, height], confidence, "person"))

        # Update tracker with the current frame's detections
        tracked_objects = tracker.update_tracks(detections, frame=frame)

        current_frame_people = 0  # Count people in the current frame

        # Process tracked objects
        for track in tracked_objects:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue  # Skip unconfirmed tracks

            x1, y1, x2, y2 = map(int, track.to_tlbr())  # Get bounding box
            obj_id = track.track_id  # Get the unique ID

            # If the ID is new, add it to the unique set
            if obj_id not in unique_person_ids:
                unique_person_ids.add(obj_id)

            # Draw bounding box and label with the unique ID
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Person {obj_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2, cv2.LINE_AA)

            current_frame_people += 1

        # Display people count for the frame and total unique people
        frame_text = f"People in Frame: {current_frame_people}"
        unique_count_text = f"Total Unique People: {len(unique_person_ids)}"
        cv2.putText(frame, frame_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, unique_count_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 255), 2, cv2.LINE_AA)

        # Display the frame
        cv2.imshow("YOLO + DeepSORT Tracking", cv2.resize(frame, (960, 540)))

        # Press 'q' to quit the video early
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_num += 1

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print(f"Total unique people detected in the video: {len(unique_person_ids)}")

# Example usage
video_path = 'videos/3.mp4'  # Replace with your video path
count_and_display_people(video_path)
