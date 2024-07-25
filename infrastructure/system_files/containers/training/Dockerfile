
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.2.0-gpu-py310-cu121-ubuntu20.04-sagemaker as base

RUN apt-get update \
 && apt-get install -y --no-install-recommends --allow-unauthenticated \
    jq git gcc libgl1-mesa-dev wget gsutil libglib2.0-0

## fix /usr/local/cuda-10.0/compat/libcuda.so
## RUN bash -c 'echo "/usr/local/cuda-10.0/compat" > /etc/ld.so.conf.d/cuda.conf'
RUN ldconfig -v
RUN pip install tensorboard torch torchvision --upgrade


FROM base as yolo

# /opt/ml and all subdirectories are utilized by SageMaker, we use the /code subdirectory to store our user code.
WORKDIR /opt/ml/code

ENV PATH="/opt/ml/code:${PATH}"

RUN git clone https://github.com/ultralytics/yolov5
RUN pip install -r yolov5/requirements.txt


FROM yolo as training

COPY train /opt/ml/code

ADD . /opt/ml/code
# COPY input/data.yaml /opt/ml/data.yaml
# COPY input/config/train_arguments.json /opt/ml/input/train_arguments.json

COPY changehostname.c /opt/ml/code/changehostname.c
COPY start_with_right_hostname.sh /usr/local/bin/start_with_right_hostname.sh

RUN chmod 777 -R /opt/ml


WORKDIR /opt/ml/code/

# this environment variable is used by the SageMaker PyTorch container to determine our user code directory.
ENV SAGEMAKER_SUBMIT_DIRECTORY /opt/ml/code

# this environment variable is used by the SageMaker PyTorch container to determine our program entry point
# for training and serving.
# For more information: https://github.com/aws/sagemaker-pytorch-container
ENV SAGEMAKER_PROGRAM train
