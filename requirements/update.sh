#!/usr/bin/env bash
set -e
for i in autoformat base compose flake8 freeze prospector pylint system_tests unit; do
    echo item: $i
    freeze-requirements freeze -m "${1:-.}"/$i.txt "${1:-.}"/$i.in
done
