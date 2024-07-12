import os
import json
import time
import logging
import os
import torch
from PIL import Image
import boto3
import os
from urllib.parse import urlparse
import numpy as np
import cv2
import torch
import numpy as np
import base64

import logging
logger = logging.getLogger(__name__)

PATH_IMGS_TEMP = '/home/raw-data'
JSON_CONTENT_TYPE = "application/json"

class ModelHandler(object):
    """
    A YOLOV5 Model handler implementation.
    """
    def __init__(self):
        
        self.initialized = False

        # Parameters for inference
        self.model = None

        # Parameters for pre-processing
        self.imgsz = 640 # default value for this usecase. 
        self.stride = 32 # default value for this usecase( differs based on the model selected )
        
        # Parameters for post-processing
        self.conf = 0.25
        self.iou = 0.45
        self.max_det = 300
        self.classes = None
        self.agnostic = False
        self.labels = {0: 'somke', 1: 'fire'}
 
        self.path = '/home/raw-data/'

    def initialize(self, context):
        print('Inititalizing')
        self.initialized = True
        properties = context.system_properties
        model_dir = properties.get("model_dir")
        
        self.model = torch.hub.load(
            'ultralytics/yolov5',
            'custom', 
            path=os.path.join(model_dir, 'best.pt'), 
            force_reload=True, 
            trust_repo=True
        )
        # print(se)
        print('Model loaded')

    def load_image_from_local_path_to_array(self, local_path):
        return np.asarray(Image.open(local_path))
        
    def download_image_from_s3(self, s3_image_uri, output_path):
        # Parse the S3 URI to get bucket name and key
        parsed_url = urlparse(s3_image_uri)
        bucket_name = parsed_url.netloc
        key = parsed_url.path.lstrip('/')

        print(parsed_url)
        print(bucket_name)
        print(key)
        print(output_path)

        # Initialize S3 client
        s3_client = boto3.client('s3')

        # Download the image file
        try:
            s3_client.download_file(bucket_name, key, output_path)
            print(f"Image downloaded successfully to: {output_path}")
        except Exception as e:
            print(f"Error downloading image: {e}")


    def input_fn(self, request_body):
        logger.info('Deserializing the input data.')
        logger.info(request_body)
        logger.info(type(request_body))
        # logger.info(request_body[0])
        # logger.info(request_body[0]['body'])
        # logger.info(base64.b64decode(bytearray_string[0]['body']))
        s3_image_uri = json.loads(request_body[0]['body'])['s3_uri']
        logger.info(f'Image s3 uri: {s3_image_uri}')

        img_name = s3_image_uri.split('/')[-1]
        img_path = f'{PATH_IMGS_TEMP}/{img_name}'
        self.download_image_from_s3(s3_image_uri, img_path)
        # image = self.load_image_from_local_path_to_array(img_path)
        
        # image = cv2.resize(image, (640, 640))
        # image_trasnp = np.transpose(np.expand_dims(image, 0), (0, 3, 1, 2))

        return img_path


    def predict_fn(self, input_data):
        logger.info('Generating prediction based on input parameters.')
        start = time.perf_counter()
        img = Image.open(input_data) 
        # results = self.model([img], size=640) # batch of images | size was givin an error
        results = self.model([img]) # batch of images
        end = time.perf_counter()
        prediction_time = end-start
        logger.info(f"Time: {prediction_time} s")
        
        return results #, prediction_time

    def upload_file_to_s3(self, local_file_path, s3_uri):
        # Parse the S3 URI to get bucket name and key
        parsed_url = urlparse(s3_uri)
        bucket_name = parsed_url.netloc
        key = parsed_url.path.lstrip('/')

        # Initialize S3 client
        s3_client = boto3.client('s3')

        # Upload the file
        try:
            s3_client.upload_file(local_file_path, bucket_name, key)
            print(f"File uploaded successfully to: {s3_uri}")
        except Exception as e:
            print(f"Error uploading file: {e}")



    def output_fn(self, inference_output, accept='application/json'):
        logger.info('Serializing the generated output.')
        # prediction, prediction_time = inference_output
        prediction = inference_output
        # logger.info("output", output)
        output = [prediction.pandas().xyxy[0].to_dict()]
        # self.upload_file_to_s3(PATH_IMGS_TEMP, DETECTS_S3_LOCATION)


        if accept == 'application/json':
            return [json.dumps(output)] #, json.dumps(prediction_time)]
        raise Exception(f'Requested unsupported ContentType in Accept: {accept}')

        # return json.loads(json.dumps(output)), response_content_type


    def handle(self, data, context):
        preprocessed_data = self.input_fn(data)
        if preprocessed_data:
            # org_input, model_input, device = preprocessed_data
            inference_output = self.predict_fn(preprocessed_data)
        return self.output_fn(inference_output,JSON_CONTENT_TYPE)

_service = ModelHandler()

def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)
    
    if data is None:
        return None

    return _service.handle(data, context)
