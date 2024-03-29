# -*- coding: utf-8 -*-
"""Data_Pre_Process.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nD4qOcUjl1f2HMUe_9n8yWs3qeMtrobA
"""

!pip install moviepy

!pip install mediapipe

import pandas as pd
import numpy as np
import moviepy.editor as mp
from datetime import datetime
import cv2
import mediapipe as mp
import csv

vid_df = pd.read_csv("video10.csv")

CLIP_LENGTH = 3

vid_df.head()

def get_time_diff(ts1, ts2):

  # Convert timestamps to datetime objects, assuming a default date
  time_format = "%M:%S"
  time1 = datetime.strptime(ts1, time_format)
  time2 = datetime.strptime(ts2, time_format)

  # Calculate the difference in seconds
  difference_in_seconds = abs((time1 - time2).total_seconds())
  return difference_in_seconds

  # Convert the difference back to 'mm:ss' format
  # minutes, seconds = divmod(difference_in_seconds, 60)
  # diff_in_mm_ss = f"{int(minutes):02d}:{int(seconds):02d}"

  # return diff_in_mm_ss

def get_new_end_time(ts, delta_s):
  # Convert timestamps to datetime objects, assuming a default date
  time_format = "%M:%S"
  time1 = datetime.strptime(ts, time_format)
  time2 = datetime.strptime("00:00", time_format)
  end_ts = (time1-time2).total_seconds() + delta_s
  # Convert the difference back to 'mm:ss' format
  minutes, seconds = divmod(end_ts, 60)
  end_ts_mm_ss = f"{int(minutes):02d}:{int(seconds):02d}"
  return end_ts_mm_ss

vid_df["time_diff_s"] = vid_df.apply(lambda x: get_time_diff(x["Start"], x["End"]), axis=1)

vid_df = vid_df[vid_df["time_diff_s"] >= CLIP_LENGTH]

new_recs = []
for _, row in vid_df.iterrows():
  new_recs_to_make = int(row["time_diff_s"]) // CLIP_LENGTH
  delta_s_list = [CLIP_LENGTH*i for i in range(1,new_recs_to_make+1)]
  new_ts_list = [row["Start"]]+ [get_new_end_time(row["Start"], delta_s) for delta_s in delta_s_list]
  ts_pairs = [(new_ts_list[i],new_ts_list[i+1]) for i in range(len(new_ts_list)-1)]
  # print(ts_pairs)
  # Set Start, End, and time_diff_s in new records
  for ts_pair in ts_pairs:
    base_rec = dict(row).copy()
    base_rec["time_diff_s"] = 3
    base_rec.update({
        "Start": ts_pair[0],
        "End":ts_pair[1]
    })
    new_recs.append(base_rec)
# print(new_recs)

final_df_per_file = pd.DataFrame(new_recs).drop("time_diff_s", axis=1)

final_df_per_file

# Write back to new_file
final_df_per_file.to_csv("clipped_Video_10.csv", index=False)

!mkdir "video_clips/"
!mkdir "audio_clips/"
!mkdir "video_clips/Video_10"
!mkdir "audio_clips/Video_10"

# Read clipped csv
df = pd.read_csv("clipped_Video_10.csv")
df.head()

def get_clip(start_ts, end_ts, video):
  """
  Accepts start and end ts in mm:ss format and a moviepy video object
  Writes a clip to storage
  """
  clip = video.subclip(start_ts, end_ts)
  clip.write_videofile(f"video_clips/Video_10/clip_{start_ts}_{end_ts}.mp4")

  # Extract the audio from the clip
  audio = clip.audio

  # Save the audio to a file
  audio.write_audiofile(f"audio_clips/Video_10/clip_{start_ts}_{end_ts}.mp3")

video = mp.VideoFileClip("Video10.mp4")

df.apply(lambda x: get_clip(x["Start"], x["End"], video), axis=1)

clip = "/content/video_clips/Video_10/clip_00:28_00:31.mp4"

def generate_landmark_csv(clip):

  # Initialize MediaPipe FaceMesh
  mp_face_mesh = mp.solutions.face_mesh
  face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                    max_num_faces=1,
                                    min_detection_confidence=0.5,
                                    min_tracking_confidence=0.5)

  # Open video file
  cap = cv2.VideoCapture(clip)

  # Prepare CSV file for writing face landmarks data
  with open(f'{clip.split(".")[0]}_face.csv', mode='w', newline='') as file:
      csv_writer = csv.writer(file)
      # Write header with landmark indices (assuming 468 landmarks per face for FaceMesh)
      header = ['frame_id'] + [f'x{i}' for i in range(468)] + [f'y{i}' for i in range(468)] + [f'z{i}' for i in range(468)]
      csv_writer.writerow(header)

      frame_id = 0
      while cap.isOpened():
          ret, frame = cap.read()
          if not ret:
              break

          # Convert the frame to RGB
          frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

          # Process the frame
          results = face_mesh.process(frame_rgb)

          # Check if landmarks were detected and write to CSV
          if results.multi_face_landmarks:
              for face_landmarks in results.multi_face_landmarks:
                  # Flatten the landmark coordinates for CSV writing
                  row = [frame_id]
                  for landmark in face_landmarks.landmark:
                      # Assuming the image width, height, and depth as 1, these are relative coordinates
                      row.extend([landmark.x, landmark.y, landmark.z])
                  csv_writer.writerow(row)

          frame_id += 1

  cap.release()

    # Initialize MediaPipe Pose
  mp_pose = mp.solutions.pose
  pose = mp_pose.Pose(static_image_mode=False,
                      model_complexity=1,
                      smooth_landmarks=True,
                      min_detection_confidence=0.5,
                      min_tracking_confidence=0.5)

  # Open video file
  cap = cv2.VideoCapture(clip)

  # Prepare CSV file for writing landmarks data
  with open(f'{clip.split(".")[0]}_pose.csv', mode='w', newline='') as file:
      csv_writer = csv.writer(file)
      # Write header with landmark indices (MediaPipe Pose model provides 33 landmarks)
      header = ['frame_id'] + [f'x{i}' for i in range(33)] + [f'y{i}' for i in range(33)] + [f'z{i}' for i in range(33)] + [f'visibility{i}' for i in range(33)]
      csv_writer.writerow(header)

      frame_id = 0
      while cap.isOpened():
          ret, frame = cap.read()
          if not ret:
              break

          # Convert the frame to RGB
          frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

          # Process the frame
          results = pose.process(frame_rgb)

          # Check if landmarks were detected and write to CSV
          if results.pose_landmarks:
              # Flatten the landmark coordinates for CSV writing
              row = [frame_id]
              for landmark in results.pose_landmarks.landmark:
                  # Pose landmarks include x, y, z coordinates and a visibility score
                  row.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])
              csv_writer.writerow(row)

          frame_id += 1

  cap.release()

generate_landmark_csv(clip)

!zip sample_data.zip sample_data/

