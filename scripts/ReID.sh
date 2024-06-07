#!/bin/bash

# Store features for all cameras.
directory=data/image
file_names=("cameraA" "cameraB" "cameraC")

for name in "${file_names[@]}"; do
  echo "$name"
  python3 ReID/extract_feature/extract_tracklet_feature.py "$directory/$name.npy" ReID/weight/model.pt "$name"
done

