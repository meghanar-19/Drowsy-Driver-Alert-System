import requests
import json
import time
import sys
from threading import Thread

import numpy as np
import cv2
import dlib
from scipy.spatial import distance as dist
import pyglet
import pygame
import geocoder


def play_alarm():
    foo = pyglet.media.load("/home/souvik/Downloads/alarm3.mp3")
    foo.play()

    def exiter(dt):
        pyglet.app.exit()
    # print("Song length is: %f" % foo.duration)
    pyglet.clock.schedule_once(exiter, foo.duration)
    pyglet.app.run()


def play_alarm2():
    pygame.mixer.init()
    sound = pygame.mixer.Sound("/home/souvik/Downloads/alarm_beep.wav")
    sound.play()
    time.sleep(4)


def get_current_location(g_maps_url):
    g = geocoder.ip('me')
    lat = g.latlng[0] + 2.64
    long = g.latlng[1] + 1.3424
    #print(lat, long)
    current_location = g_maps_url.format(lat, long)
    return current_location


JAWLINE_POINTS = list(range(0, 17))
RIGHT_EYEBROW_POINTS = list(range(17, 22))
LEFT_EYEBROW_POINTS = list(range(22, 27))
NOSE_POINTS = list(range(27, 36))
RIGHT_EYE_POINTS = list(range(36, 42))
LEFT_EYE_POINTS = list(range(42, 48))
MOUTH_OUTLINE_POINTS = list(range(48, 61))
MOUTH_INNER_POINTS = list(range(61, 68))

EYE_AR_THRESH = 0.22
EYE_AR_CONSEC_FRAMES = 6
EAR_AVG = 0

CONTINUOUS_FRAMES = True
COUNTER = 0
TOTAL = 0
ALARM_ON = False
g_maps_url = "http://maps.google.com/?q={},{}"

def eye_aspect_ratio(eye):
    # compute the euclidean distance between the vertical eye landmarks
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])

    # compute the euclidean distance between the horizontal eye landmarks
    C = dist.euclidean(eye[0], eye[3])

    # compute the EAR
    ear = (A + B) / (2 * C)
    return ear

# to detect the facial region
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

# capture video from live video stream
cap = cv2.VideoCapture(0)
while CONTINUOUS_FRAMES:
    # get the frame
    ret, frame = cap.read()
    #frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    if ret:
        # convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)
        for rect in rects:
            x = rect.left()
            y = rect.top()
            x1 = rect.right()
            y1 = rect.bottom()
            # get the facial landmarks
            landmarks = np.matrix([[p.x, p.y] for p in predictor(frame, rect).parts()])
            # get the left eye landmarks
            left_eye = landmarks[LEFT_EYE_POINTS]
            # get the right eye landmarks
            right_eye = landmarks[RIGHT_EYE_POINTS]
            # draw contours on the eyes
            left_eye_hull = cv2.convexHull(left_eye)
            right_eye_hull = cv2.convexHull(right_eye)
            cv2.drawContours(frame, [left_eye_hull], -1, (0, 255, 0), 1) # (image, [contour], all_contours, color, thickness)
            cv2.drawContours(frame, [right_eye_hull], -1, (0, 255, 0), 1)
            # compute the EAR for the left eye
            ear_left = eye_aspect_ratio(left_eye)
            # compute the EAR for the right eye
            ear_right = eye_aspect_ratio(right_eye)
            # compute the average EAR
            ear_avg = (ear_left + ear_right) / 2.0
            # detect the eye blink
            if ear_avg < EYE_AR_THRESH:
                COUNTER += 1
                print(COUNTER)
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    #TOTAL += 1
                    #print("Eye blinked")
                    if not ALARM_ON:
                        ALARM_ON = True
                        t = Thread(target=play_alarm2)
                        t.daemon = True
                        t.start()
                    # draw an alarm on the frame
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if COUNTER >= 25:
                    print("Something wrong?")
                    CONTINUOUS_FRAMES = False
                    break

            else:
                COUNTER = 0
                ALARM_ON = False

            #cv2.putText(frame, "Blinks{}".format(TOTAL), (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 1)
            cv2.putText(frame, "EAR {}".format(ear_avg), (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 1)
        cv2.imshow("Winks Found", frame)
        key = cv2.waitKey(1) & 0xFF
        # When key 'Q' is pressed, exit
        if key is ord('q'):
            break


# release all resources
cap.release()
# destroy all windows
cv2.destroyAllWindows()

# send message to the person's 5 immediate contacts
current_location = get_current_location(g_maps_url)
print(current_location)
sys.exit()

