cd ~/amazon-kinesis-video-streams-producer-sdk-cpp/build


export AWS_KINESISVIDEO_IMAGE_GENERATION=""
export GST_PLUGIN_PATH="$(pwd)/../build"
export LD_LIBRARY_PATH="$(pwd)/../open-source/local/lib"
export IOT_REQUEST_CONNECTION_TIMEOUT=100000
export CERT_PATH=certs/certificate_camera_001.pem.crt
export PRIVATE_KEY_PATH=certs/private_camera_001.pem.key
export CA_CERT_PATH=certs/AmazonRootCA1.pem
export ROLE_ALIAS=CameraIoTRoleAlias
export IOT_GET_CREDENTIAL_ENDPOINT=c2w9kquumpl5ix.credentials.iot.us-east-1.amazonaws.com
export IOT_THING_NAME=camera_001

export AWS_DEFAULT_REGION= 
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=


# token login
# gst-launch-1.0 -v rtspsrc location=rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream latency=100 protocols=tcp ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! x264enc ! h264parse ! kvssink stream-name="camera_001" access-key=$AWS_ACCESS_KEY_ID secret-key=$AWS_SECRET_ACCESS_KEY aws-region=$AWS_DEFAULT_REGION kms_key_id="camera_001"

# iot credentials login
gst-launch-1.0 -v rtspsrc location=rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream latency=100 protocols=tcp ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! x264enc ! h264parse ! kvssink stream-name="$IOT_THING_NAME" aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"


# stream file - not working
gst-launch-1.0 -v filesrc location=0191FE6F-20231030HighlandFireRiverside30fps.h264 ! h264parse ! rtph264pay pt=96 config-interval=1 ! application/x-rtp,media=video,encoding-name=H264,payload=96 ! kvssink stream-name="$IOT_THING_NAME" aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"

gst-launch-1.0 -v filesrc location=0191FE6F-20231030HighlandFireRiverside30fps.h264 ! video/x-h264,width=1920,height=1080,framerate=30/1,profile=constrained-baseline ! h264parse  ! kvssink stream-name="$IOT_THING_NAME" aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"

gst-launch-1.0 -v filesrc location=0191FE6F-20231030HighlandFireRiverside30fps.h264 ! h264parse ! rtph264pay name=pay0 pt=96 ! udpsink host=127.0.0.1 port=5004

gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:5004/h264 ! rtph264depay ! decodebin ! autovideosink
                     
gst-launch-1.0 -v filesrc location=0191FE6F-20231030HighlandFireRiverside30fps.h264 ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! x264enc ! h264parse ! kvssink stream-name="$IOT_THING_NAME" aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"




# trying example script
./kvs_gstreamer_sample "$IOT_THING_NAME" rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"
./kvs_gstreamer_sample "$IOT_THING_NAME" 0191FE6F-20231030HighlandFireRiverside30fps.h264 aws-region=$AWS_DEFAULT_REGION iot-certificate="iot-certificate,endpoint=$IOT_GET_CREDENTIAL_ENDPOINT,cert-path=$CERT_PATH,ca-path=$CA_CERT_PATH,role-aliases=$ROLE_ALIAS,iot-thing-name=$IOT_THING_NAME,key-path=$PRIVATE_KEY_PATH"

./kvs_gstreamer_sample "$IOT_THING_NAME" /home/martin/Projects/ongoing/ukw/data/test_images/20231030_Highland_Fire_Riverside_30fps.mp4 aws-region=$AWS_DEFAULT_REGION access-key=$AWS_ACCESS_KEY_ID secret-key=$AWS_SECRET_ACCESS_KEY aws-region=$AWS_DEFAULT_REGION

./kvs_gstreamer_sample "$IOT_THING_NAME" aws-region=$AWS_DEFAULT_REGION access-key=$AWS_ACCESS_KEY_ID secret-key=$AWS_SECRET_ACCESS_KEY


AWS_ACCESS_KEY_IDy=$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY ./kvs_gstreamer_sample $IOT_THING_NAME 0191FE6F-20231030HighlandFireRiverside30fps.h264

./kvs_gstreamer_sample camera_001 rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream







gst-launch-1.0 -v rtspsrc location=rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream latency=100 protocols=tcp ! rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! x264enc ! h264parse ! kvssink stream-name=camera_001 aws-region=us-east-1 iot-certificate=iot-certificate,endpoint=c2w9kquumpl5ix.credentials.iot.us-east-1.amazonaws.com,cert-path=certs/certificate-camera_001.pem.crt,ca-path=certs/AmazonRootCA1.pem,role-aliases=CameraIoTRoleAlias,iot-thing-name=camera_001


gst-launch-1.0 rtspsrc location=rtsp://soft:FTP2023sof@45.171.132.165:554/h264/ch1/main/av_stream short-header=TRUE ! rtph264depay ! video/x-h264,format=avc,alignment=au ! h264parse ! kvssink 
