# Nanowire Tracker
GUI for tracking objects using lighting threshold and motion combined with mask

##### Method:
1. Apply a threshold filter to obtain the objects of interest
2. Take a snapshot of the first frame in the video where I assume all the pixels are stationary and use that to ignore any pixels that overlap into the same area
3. Apply the motion filter to obtain all the pixels that seem to be moving i.e. the nanowire. 
4. The two filtered frames are then combined into one to obtain an approximation on the pixels that are associated with the nanowire and a minimum area rectangle is overlaid as the bounding box. 

##### Issues
- The mask used for ignoring the spheres also view the nanowire in the first frame as a stationary object and thus occludes pixels that are in the same location. This could be fixed by taking a snapshot of the area when only the stationary objects you wish to ignore are present, or I could implement an interface for selecting the objects to ignore yourself. 
- Occasionally, there are artifacts that the motion filter identifies which leads to the bounding box not placed exactly on top of the nanowire. I found that by letting the program warm-up in a sense improves the effectiveness of it since the motion filter needs a history of frames to compare the current frame to. 
- There is an edge case where if the nanowire is in contact with the spheres at an odd angle/position, the filter struggles with the occlusion ends up separating the nanowire and two bounding boxes are placed. A possible fix to this is to simply retain one bounding box and ignore any other possible bounding boxes if it pops into vicinity without other nanowires nearby. 
- The motion filter could be a little computationally heavy. The filter works well when it's running at around 30fps but I don't know how smoothly it will run at 160fps. 

## Installation
Download VideoTrack.py and run on a machine with Python 3 installed <br>
Install the following modules:
```
pip install Pillow
pip install opencv
```

## Usage
1. Go to bottom of Tracker and insert url of video to test on
2. Save and run file
3. GUI should appear. Adjust sliders to find satisfactory setting:
- **Threshold**: Sets bound for which to ignore pixels with values less than threshold
- **Blob Opacity**: Changes the opacity of the unfiltered pixels overlaid with original video
- **Mask Dilation**: Expands the mask used to ignore pixels that overlap
- **Set mask**: Takes a snippet of the current unfiltered pixels and uses that to create a mask that determines which areas to ignore 
- **Show mask**: Toggles view of the mask being used


## License
[GNU Public License v3](https://www.gnu.org/licenses/gpl-3.0.html)