import json

# import tempfile
import boto3
from twilio.rest import Client

ENDPOINT_NAME = "YOLO-V5-DEPLOYMENT"
INF_OUTPUT_BUCKET = 'ukw-wildfire-camera001-positive-cases'

TWILIO_ACCOUNT_ID = 'AC0ae0e97cd54f42c375d0639e1e4c06c6'
TWILIO_TOKEN = 'e8ff0914abbdfabd695e2f6aa4e13187'


# # utils functions
def dynamo_format_from_dict(data_dict):
    """Converts a Python dictionary into a format suitable for DynamoDB's put_item method,
    casting all values to strings.

    Args:
        data: A dictionary containing the data to be formatted.

    Returns:
        A dictionary formatted for DynamoDB, where each value is wrapped in a dictionary 
        specifying its DynamoDB data type (always 'S' in this case) and cast to a string.
    """
    return {k: {'S': str(v)} for k, v in data_dict.items()}
    
    
# Initialize S3 and SageMaker clients
s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')
s3_resource = boto3.resource('s3')


# def save_image_to_temp(image_data, image_format="JPEG"):
#     """Saves image data to a temporary file in the Lambda /tmp directory."""

#     with tempfile.NamedTemporaryFile(suffix=f".{image_format.lower()}", delete=False, dir="/tmp") as temp_file:
#         temp_file.write(image_data)
#         return temp_file.name


# Initialize S3 and SageMaker clients
dynamodb = boto3.client('dynamodb')


def lambda_handler(event, context):
    # Get the S3 bucket and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Construct the S3 URI for the image
    s3_uri = f"s3://{bucket}/{key}"

    # Call the SageMaker endpoint with the S3 URI
    try:
        response = sagemaker_client.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,  # Replace with your endpoint name
            ContentType='application/json',
            # Body=json.dumps(s3_uri)
            Body=json.dumps({'s3_uri': s3_uri})
        )
        result = json.loads(response['Body'].read().decode('utf-8'))
        print(f"SageMaker prediction: {result}")

    except Exception as e:
        print(f"Error calling SageMaker endpoint: {e}")
        return


    if len(result[0]['xmin']) > 0:
        try:
            # copy_source = {
            #     'Bucket': bucket,
            #     'Key': key
            #  }
            # s3_resource.meta.client.copy(copy_source, INF_OUTPUT_BUCKET, key)
        
            dynamodb.put_item(
                TableName='wildfire_camera_001_preds', 
                Item={
                        'model_id': {'S': 'yolov5s_v1'},
                        'camera_id': {'S': '001'},
                        'image_id': {'S': key},
                        'prediction': {'M': dynamo_format_from_dict(result[0])}
                    }
                )
                
            print('Prediction saved! - {key}')

        except Exception as e2:
            print(f"Upload to DynamoDB failed: {e2}")

        try:
            account_sid = 'AC0ae0e97cd54f42c375d0639e1e4c06c6'
            auth_token = 'e8ff0914abbdfabd695e2f6aa4e13187'
            client = Client(account_sid, auth_token)
            

            # image_url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': key}, ExpiresIn = 100)

            print('Sending whatsapp via Twilio')

            message = client.messages.create(
                from_='whatsapp:+14155238886',
                to='whatsapp:+5219841387243',
                body=f'FUEGO! - {key}'
                # media_url=image_url, #f'https://{bucket}.s3.amazonaws.com/{key}',
            )

            print(f'Whatsapp sent! {message}')

        except Exception as e3:
            print(f"Sending whatsapp failed: {e3}")
            return

    

        

    # Do something with the prediction result (e.g., store in a database)
    # ...

    return {
        'statusCode': 200,
        'body': json.dumps('Image processed successfully.')
    }

