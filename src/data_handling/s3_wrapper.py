import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import boto3
from botocore.exceptions import ClientError


class S3Wrapper:
    def __init__(self, endpoint_url=None, aws_access_key_id=None, aws_secret_access_key=None, max_workers=5):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,  
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=boto3.session.Config(retries={'max_attempts': 5, 'mode': 'standard'})
        )
        self.max_workers = max_workers
        self.bucket_locks = {}
        self._logger = logging.getLogger(__name__)

    def _get_bucket_lock(self, bucket_name):
        if bucket_name not in self.bucket_locks:
            self.bucket_locks[bucket_name] = Lock()
        return self.bucket_locks[bucket_name]

    def create_bucket(self, bucket_name):
        with self._get_bucket_lock(bucket_name):  # Lock since bucket creation is not idempotent
            try:
                self.s3.create_bucket(Bucket=bucket_name)
                self._logger.info(f"Created bucket: {bucket_name}")
            except ClientError as e:
                self._logger.error(f"Error creating bucket '{bucket_name}': {e}")
                raise 

    def upload_file(self, file_name, bucket_name, object_name=None):
        # No locking here as S3 handles concurrent uploads of the same object
        if object_name is None:
            object_name = file_name

        try:
            self.s3.upload_file(file_name, bucket_name, object_name)
            self._logger.info(f"Uploaded file '{file_name}' to '{bucket_name}/{object_name}'")
        except ClientError as e:
            self._logger.error(f"Error uploading file '{file_name}': {e}")
            raise 
        

    def download_file(self, bucket_name, object_name, file_name):
        # No locking here since it's a read operation
        try:
            self.s3.download_file(bucket_name, object_name, file_name)
            self._logger.info(f"Downloaded file '{object_name}' from '{bucket_name}' to '{file_name}'")
        except ClientError as e:
            self._logger.error(f"Error downloading file '{object_name}': {e}")
            raise 

    def delete_file(self, bucket_name, object_name):
        with self._get_bucket_lock(bucket_name): # Lock since delete is not idempotent
            try:
                self.s3.delete_object(Bucket=bucket_name, Key=object_name)
                self._logger.info(f"Deleted file '{object_name}' from '{bucket_name}'")
            except ClientError as e:
                self._logger.error(f"Error deleting file '{object_name}': {e}")
                raise 

    def list_objects(self, bucket_name):
        # No locking here since it's a read operation
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            self._logger.error(f"Error listing objects in bucket '{bucket_name}': {e}")
            raise 

    def delete_bucket(self, bucket_name):
        with self._get_bucket_lock(bucket_name): 
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    objects = self.list_objects(bucket_name)
                    executor.map(lambda obj: self.delete_file(bucket_name, obj), objects)
                
                self.s3.delete_bucket(Bucket=bucket_name)
                self._logger.info(f"Deleted bucket: {bucket_name}")
            except ClientError as e:
                self._logger.error(f"Error deleting bucket '{bucket_name}': {e}")
                raise
