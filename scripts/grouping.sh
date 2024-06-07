#!/bin/bash


file_names=("cameraA" "cameraB" "cameraC")

for name in "${file_names[@]}"; do
  echo "$name"
  python3 matching/grouping.py --cam "$name"
done

