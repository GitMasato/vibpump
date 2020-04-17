#!/bin/bash

python_path="python3.7"
python_file="vibration_pump.py"

movies=("glass_beads.m4v" "glass.m4v")

is_captured=true
is_rotated=false
is_cropped=false
is_binarized=false
is_measured=false
is_showed=false
is_cleaned=false

################################################################################

args=()
if [[ $is_captured == true ]]; then
  args+=("--capture")
fi
if [[ $is_rotated == true ]]; then
  args+=("--rotate")
fi
if [[ $is_cropped == true ]]; then
  args+=("--crop")
fi
if [[ $is_binarized == true ]]; then
  args+=("--binarize")
fi
if [[ $is_measured == true ]]; then
  args+=("--measure")
fi
if [[ $is_showed == true ]]; then
  args+=("--show")
fi
if [[ $is_cleaned == true ]]; then
  args+=("--clean")
fi

echo $python_path $python_file --files "${movies[@]}" "${args[@]}"
eval $python_path $python_file --files "${movies[@]}" "${args[@]}"
