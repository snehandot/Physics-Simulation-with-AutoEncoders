import cv2
import numpy as np

def calc_Range_BW(colors):
    min_color = np.min(colors, axis=0)
    max_color = np.max(colors, axis=0)
    return [max_color, min_color]

def process_frame(frame, rangeB, rangeW):
    j = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    q = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    q = cv2.medianBlur(q, 11)
    j = cv2.medianBlur(j, 5)
    centrej = cv2.cvtColor(j, cv2.COLOR_GRAY2RGB)

    # Adjust these parameters based on your observations
    minRadius = 2   # Minimum radius of detected circles
    maxRadius = 20   # Maximum radius of detected circles
    param1 = 100     # Higher threshold for Canny edge detector
    param2 = 30      # Accumulator threshold for the circle centers

    circles = cv2.HoughCircles(j, cv2.HOUGH_GRADIENT, 1, 20, param1=param1, param2=param2, minRadius=minRadius, maxRadius=maxRadius)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(centrej, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv2.circle(centrej, (i[0], i[1]), 2, (0, 0, 255), 3)
            
            if rangeB[1][1] <= q[i[1], i[0], 1] <= rangeB[0][1] and rangeB[1][0] <= q[i[1], i[0], 0] <= rangeB[0][0]:
                color = (0, 0, 0) # Black coin
            elif rangeW[1][1] <= q[i[1], i[0], 1] <= rangeW[0][1] and rangeW[1][0] <= q[i[1], i[0], 0] <= rangeW[0][0]:
                color = (255, 255, 255) # White coin
            else:
                color = (0, 0, 255) # Red coin
            
            cv2.circle(centrej, (i[0], i[1]), i[2], color, 2)

    return centrej

def main(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Unable to open video. Check the file path and try again.")
        return

    # Predefined color ranges for black and white coins
    colorBlack = np.array([[5, 5, 5], [50, 50, 50], [90, 90, 90]]) # Updated values for black
    colorWhite = np.array([[100, 100, 100], [160, 160, 160], [190, 190, 190]]) # Updated values for white

    rangeB = calc_Range_BW(colorBlack)
    rangeW = calc_Range_BW(colorWhite)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame = process_frame(frame, rangeB, rangeW)
        cv2.imshow('Detected Circles and Centres', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    video_path = '/Users/alferix/Documents/carrom/vid1.mp4'
    main(video_path)