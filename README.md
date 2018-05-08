# fitmangle

Crude tools to visualize or manipulate runs from FIT files

## Getting started

It's a bit cleaner if you set up a virtualenv first, then you can install the required packages
independently of what is installed on the computer. Install all this at once with:

    pip3 install -r requirements.txt

## Comparisonize

    python3 comparizonize.py activity_1.fit activity_2.fit ...

Note that I use a fancy footpod with many extra Connect IQ fields, so you might need to edit the
script to your needs and field availability.

## Magic Footpod positioning

    python3 magic_footpod.py activity.fit route.tcx > activity_with_position.tcx
    
If you want a prettier XML file, pipe that command line through `xmllint --format -`.
