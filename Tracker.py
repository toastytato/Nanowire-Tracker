import numpy as np
import cv2
import tkinter as tk
from PIL import ImageTk, Image


class VideoTrackWindow(tk.Frame):
    def __init__(self, parent, url, speed):
        super().__init__(parent)
        parent.title("Nanowire Tracker")

        self.window_width = 1080

        self.cap = cv2.VideoCapture(url)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(fps)
        self.period = int(1000 / (fps * speed))

        self.init_params()
        self.init_ui()
        self.base_mask = self.get_mask()  # mask used for subtracting stationary objects
        self.mod_mask = self.base_mask
        self.motion_filter = cv2.createBackgroundSubtractorKNN(history=1000, detectShadows=True)

        self.refresh()

    def init_params(self):
        self.vid_params = {
            'Threshold': {
                'value': 115,
                'min': 0,
                'max': 255,
                'step': 1, },
            'Blob Opacity': {
                'value': 1,
                'min': 0,
                'max': 1.0,
                'step': 0.01, },
            'Mask Dilation': {
                'value': 4,
                'min': 0,
                'max': 5,
                'step': 1, },
        }
        self.is_showing_mask = False

    def init_ui(self):
        # self.canvas = tk.Canvas(self, width=self.cap.get(3)/2, height=self.cap.get(4)/2)
        # self.canvas.grid(row=0, column=0, columnspan=2)
        video_frame = tk.Frame(self)
        self.panel = tk.Label(video_frame)
        self.panel.pack()
        video_frame.pack(side=tk.LEFT)

        controls_frame = tk.Frame(self)

        sliders_frame = tk.Frame(controls_frame)

        self.sliders = {}
        for i, (name, slider) in enumerate(self.vid_params.items()):
            label = tk.Label(sliders_frame, text=name)
            label.grid(row=i, column=0, sticky=tk.E)

            self.sliders[name] = tk.Scale(sliders_frame,
                                          from_=slider['min'],
                                          to=slider['max'],
                                          resolution=slider['step'],
                                          orient=tk.HORIZONTAL,
                                          length=150)
            self.sliders[name].set(slider['value'])
            self.sliders[name].grid(row=i, column=1, sticky=tk.W)
        sliders_frame.pack()

        self.set_mask_btn = tk.Button(controls_frame,
                                      text='Set Mask',
                                      command=self.set_mask_event)
        self.show_mask_btn = tk.Button(controls_frame,
                                       text='Show Mask',
                                       command=self.show_mask_event)
        self.set_mask_btn.pack(pady=5)
        self.show_mask_btn.pack(pady=5)

        controls_frame.pack(side=tk.RIGHT)

    def refresh(self):
        self.update_params()

        ret, frame = self.cap.read()

        if ret:

            # process frame returns blobbed imgs as well as drawing tracking box onto frame
            regions_of_interest, tracker_frame = self.process(frame)

            img1_opacity = float(self.vid_params['Blob Opacity']['value'])
            img2_opacity = 1 - img1_opacity

            weighted = cv2.addWeighted(regions_of_interest, img1_opacity, frame, img2_opacity, 0.0)
            final = frame
            # overlay the regions of interest
            final[regions_of_interest > 0] = weighted[regions_of_interest > 0]
            # overlay the tracker frame
            final[tracker_frame > 0] = 255

            if self.is_showing_mask:
                mask = cv2.bitwise_not(self.mod_mask)
                final[mask > 0] = (255, 0, 0)

            self.display_frame(final)
        else:
            # print("bad")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        #
        # if cv2.waitKey(0) == ord(' '):
        #     root.quit()

        root.after(self.period, self.refresh)

    def display_frame(self, frame):
        img = Image.fromarray(frame)

        # fit frame to desired window size
        scaling = (self.window_width / float(img.size[0]))
        height = int((float(img.size[1] * float(scaling))))
        img = img.resize((self.window_width, height), Image.ANTIALIAS)

        img = ImageTk.PhotoImage(img)
        self.panel.configure(image=img)
        self.panel.image = img

    def update_params(self):
        for key, value in self.vid_params.items():
            self.vid_params[key]['value'] = self.sliders[key].get()

    def set_mask_event(self, event=None):
        self.base_mask = self.get_mask()
        self.mod_mask = self.base_mask

    def show_mask_event(self, event=None):
        if self.is_showing_mask:
            self.is_showing_mask = False
            self.show_mask_btn.config(relief=tk.RAISED)
        else:
            self.is_showing_mask = True
            self.show_mask_btn.config(relief=tk.SUNKEN)

    def get_mask(self, event=None):
        ret, frame = self.cap.read()

        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, thresh = cv2.threshold(gray, self.vid_params['Threshold']['value'], 255,
                                        cv2.THRESH_BINARY)
            #  thresh = cv2.bitwise_not(thresh)
            # thresh = cv2.erode(thresh, None, iterations=2)
            return thresh

        return None

    # get a mask with the motion filter
    # apply mask on threshold
    # only get
    def process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # get only pixels above a certain value
        ret, thresh = cv2.threshold(gray, self.vid_params['Threshold']['value'], 255, cv2.THRESH_BINARY)
        thresh = cv2.bitwise_not(thresh)
        thresh = cv2.dilate(thresh, None, iterations=2)
        thresh = cv2.erode(thresh, None, iterations=2)

        # ignore masked out pixels
        if self.mod_mask is not None:
            self.mod_mask = cv2.erode(self.base_mask, None, iterations=self.vid_params['Mask Dilation']['value'])
            thresh = cv2.bitwise_and(self.mod_mask, thresh)
            thresh = cv2.dilate(thresh, None, iterations=2)

        # use motion filter
        motion = self.motion_filter.apply(gray)
        # filter noise
        kernel = np.ones((3, 3), np.uint8)
        motion = cv2.erode(motion, kernel, iterations=1)
        motion = cv2.dilate(motion, kernel, iterations=3)

        # combine the values of both the thresh (masked) filter and motion filter
        combined = cv2.bitwise_or(thresh, motion)

        colored = cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR)
        # put a bounding box on the final frame
        tracker_frame = np.zeros(colored.shape)
        contours, hierarchy = cv2.findContours(combined, 1, 2)
        for cnt in contours:
            if cv2.contourArea(cnt) < 150:
                continue
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(tracker_frame, [box], 0, (0, 255, 0), 2)

        return colored, tracker_frame


if __name__ == "__main__":
    # insert video url here
    # if url is in same folder, it should just be the name of the video
    # for eg:
    # url = 'wires-fixedSphere_original.avi'
    url = ""

    # how fast to play back the footage
    # doesn't necessarily follow through, bottle-necked by the video processing
    playback_speed = 4

    # start gui
    root = tk.Tk()
    VideoTrackWindow(root, url, playback_speed).pack()
    root.mainloop()
