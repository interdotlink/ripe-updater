# -*- coding: utf-8 -*-

import os
import boto3

from botocore.exceptions import ClientError

from .log_manager import LogManager
from .configuration import *


class BackupManager:
    """
    Handles storage of backups for ripe objects
    """
    def __init__(self):
        """
        connect to s3 and ensures presence of the bucket
        """
        self.logger = LogManager().logger

        if S3_BACKUP == 'yes':
            self.logger.info(f"connect to s3 {S3_ENDPOINT_URL}")
            self.s3 = boto3.client(
                service_name='s3',
                endpoint_url=S3_ENDPOINT_URL,
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_ACCESS_KEY
            )

            try:
                self.logger.info(f"creating bucket {S3_BUCKET}")
                self.s3.create_bucket(Bucket=S3_BUCKET)
            except ClientError as error:
                if error.response['Error']['Code'] == 'BucketAlreadyExists':
                    self.logger.info("bucket already exists")
                else:
                    raise error
        else:
            self.logger.info("S3-Backup disabled")

    def put(self, filename, content):
        """
        upload an object to s3
        """
        if S3_BACKUP == 'yes':
            return self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=filename,
                Body=content
            )
        
        return None

    def get(self, filename):
        """
        return the content of an object
        """
        if S3_BACKUP == 'yes':
            return self.s3.get_object(
                Bucket=S3_BUCKET,
                Key=filename
            )['Body'].read()
        
        return ""

    def list(self):
        """
        list all objects in this bucket
        """
        if S3_BACKUP == 'yes':
            files = self.s3.list_objects(Bucket=S3_BUCKET)
            self.logger.debug(f'{files=}')
            if files.get('Contents'):
                return [o['Key'] for o in files['Contents']]
        
        return []

