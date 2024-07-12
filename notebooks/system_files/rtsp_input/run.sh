docker build -t video-sampler . && \  # comentar linea si ya esta la imagen creada
docker run --env-file .env \
-v ./videos:/app/videos \
video-sampler \
rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream \  # video source. If file, it should start with "./videos/"...
2 \  # n of frames per second
ukw-wildfire-camera001-samples # s3 bucket name
