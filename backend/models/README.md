# Face detector model files (for the real CV path)

The synthetic demo needs nothing here. To run real video redaction, download
OpenCV's res10 SSD face detector into this folder:

- deploy.prototxt
  https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt
- res10_300x300_ssd_iter_140000.caffemodel
  https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel

Then:  export OBSCURA_VIDEO=/path/to/clip.mp4   and restart uvicorn.
