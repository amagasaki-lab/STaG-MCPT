#!/bin/bash

python3 data/img2npy.py --input_video_path data/movie/cameraA.mp4  --cam cameraA  --start_frame 1 --end_frame 18000

python3 data/img2npy.py --input_video_path data/movie/cameraB.mp4  --cam cameraB  --start_frame 1 --end_frame 18000

python3 data/img2npy.py --input_video_path data/movie/cameraC.mp4  --cam cameraC  --start_frame 1 --end_frame 18000