import collections
import time
from queue import Queue
from threading import Thread
from vidgear.gears import CamGear
import cv2
from imutils.video import FPS

# Open suitable video stream, such as webcam on first index(i.e. 0)


cv2.namedWindow("Output", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Output", 1920, 1080)
cv2.setWindowProperty("Output", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
Q = Queue(maxsize=128)

class FileVideoStream:
    def __init__(self, path, transform=None, queue_size=128):
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        self.stream = CamGear(source=path).start()
        self.stopped = False
        self.transform = transform
        self.resolution = (1920, 1080)
        self.c_frame = None
        # initialize the queue used to store frames read from
        # the video file
        self.Q = collections.deque(maxlen=queue_size)
        # intialize thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.vid_fps = self.stream.framerate

    def start(self):
        # start a thread to read frames from the file video stream
        self.thread.start()
        return self

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                break
            #print(len(self.Q))
            # otherwise, ensure the queue has room in it
            if not len(self.Q) == self.Q.maxlen:
                # read the next frame from the file

                self.c_frame = self.stream.read()

                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
                if self.c_frame is None:
                    self.stop()

                # Transform the frame if needed
                if self.resize:
                    self.c_frame = self.resize()

                # add the frame to the queue
                self.Q.appendleft(self.c_frame)
            else:
                print("Queue full")
                time.sleep(0.2)  # Rest for 100ms, we have a full queue

        self.stream.stop()

    def read(self):
        # return next frame in the queue
        return self.Q.pop()[0]

    # Insufficient to have consumer use while(more()) which does
    # not take into account if the producer has reached end of
    # file stream.
    def running(self):
        return self.more() or not self.stopped

    def more(self):
        # return True if there are still frames in the queue. If stream is not stopped, try to wait a moment
        tries = 0

        while len(self.Q) == 0 and not self.stopped and tries < 5:
            time.sleep(0.1)
            tries += 1
        return len(self.Q) > 1

    def resize(self):
        self.c_frame = (self.c_frame, self.resolution)
        return self.c_frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
        # wait until stream resources are released (producer thread might be still grabbing frame)
        self.thread.join()


fs = FileVideoStream("C:/Python_Projekte/Persönlich/Better Gallery/bin/4k60fps_1.mp4").start()
fps = FPS()
fps.start()
time.sleep(5)
timer = time.time()
fpss = ((1 / 30) * 1000) / 2

while True:
    timfps = time.time()
    fps.update()
    if fs.running() and fs.more():
        frame = fs.read()
    else:
        break

    cv2.imshow("Output", frame)

    fpss = fpss - (time.time() - timfps) * 1000
    if fpss < 1:
        print("fps too low")
        fpss = 1
    print(fpss)
    key = cv2.waitKey(int(fpss)) & 0xFF
    if key == ord("q"):
        break
print(time.time() - timer)

cv2.destroyAllWindows()
fs.stop()
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
