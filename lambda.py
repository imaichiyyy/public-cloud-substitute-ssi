import json
import os
import logging
import boto3
from botocore.errorfactory import ClientError
import re
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client('s3')
def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)
 
    input_bucket = event['Records'][0]['s3']['bucket']['name']
    output_bucket = os.environ['S3_BUCKET_TARGET']

    logger.info('## INPUT BUKET')
    logger.info(input_bucket)
    
    input_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    logger.info('## INPUT KEY')
    logger.info(input_key)

    try:
        # 入力ファイルの取得
        response = s3.get_object(Bucket=input_bucket, Key=input_key)

        if not input_key.endswith('.html'):
            s3.copy_object(Bucket=output_bucket, Key=input_key, CopySource={'Bucket': input_bucket, 'Key': input_key})
        else:
            input_html = response[u'Body'].read().decode('utf-8')
            output_html = input_html
            # SSI記述を取得
            include_path_base = re.findall(r'<!--#include virtual="/(.*?)" -->.*?\n', input_html, flags=re.DOTALL)
            logger.info('## PATH BASE')
            logger.info(include_path_base)
            if len(include_path_base) > 0:
                for path in include_path_base:
                    include_path = path
                    logger.info('## PATH')
                    logger.info(include_path)
            
                    # SSIファイルの取得
                    try:
                        # include_head = s3.head_object(Bucket=input_bucket,Key=include_path)
                        include = s3.get_object(Bucket=input_bucket, Key=include_path)
                        include_html = include[u'Body'].read().decode('utf-8')
                        # SSIを実行
                        output_html = output_html.replace('<!--#include virtual="/' + include_path + '" -->', include_html)
                    except ClientError:
                        pass
            
            # ファイル出力
            logger.info('## OUTPUT BUKET')
            logger.info(output_bucket)
            
            output_key    = input_key
            logger.info('## OUTPUT KEY')
            logger.info(output_key)
            
            out_s3   = boto3.resource('s3')
            s3_obj   = out_s3.Object(output_bucket, output_key)
            response = s3_obj.put(Body = bytes(output_html, 'UTF-8'))
    except Exception as e:
        logger.info(e)
        raise e