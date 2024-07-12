docker build -t video-sampler . && \  # comentar linea si ya esta la imagen creada
docker run --env-file .env \
-v ./videos:/app/videos \
video-sampler \
/home/martin/Projects/ongoing/ukw/data/test_images/20231030_Highland_Fire_Riverside_30fps.mp4 \  # rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream \  # video source. If file, it should start with "./videos/"...
2 \  # n of frames per second
ukw-wildfire-camera001-samples # s3 bucket name 

