import json
import os
import logging
import oss2 
import re
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 作業サマリー
# データをアップする作業者は src/ 内のディレクトリにデータを格納してください
# 公開ディレクトリ、またはCDNへ接続するディレクトリは dist/ 内をルート直下として設定してください

# 設定（埋めてください）
OSS_ENDPOINT        = "" # OSSのエンドポイント（OSSの管理画面上「概要」の中の「アクセスドメイン名」に記載のあるエンドポイントを記載
DEST_BUCKET_NAME    = "" # バケット名を記載
SOURCE_DIRECTORY    = "src/" # データをアップする領域
DIST_DIRECTORY      = "dist/" # 公開ディレクトリ、またはCDNへ接続するディレクトリ

def handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)
    
    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId, creds.accessKeySecret, creds.securityToken)
    evt = json.loads(event)
 
    input_bucket = oss2.Bucket(auth, OSS_ENDPOINT, DEST_BUCKET_NAME)

    logger.info('## INPUT BUKET')
    logger.info(input_bucket)
    
    input_key = urllib.parse.unquote_plus(evt['events'][0]['oss']['object']['key'])
    logger.info('## INPUT KEY')
    logger.info(input_key)

    try:
        # 入力ファイルの取得
        response = input_bucket.get_object(input_key)
        logger.info(response)

        output_key    = re.sub('^'+ SOURCE_DIRECTORY, DIST_DIRECTORY,input_key)
        logger.info('## OUTPUT KEY')
        logger.info(output_key)

        if not input_key.endswith('.html'):
            logger.info(response)
            input_bucket.put_object(output_key, response)

        else:
            input_html = response.read().decode('utf-8')
            logger.info('## input_html')
            logger.info(input_html)
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
                        include = input_bucket.get_object('src/' + include_path)
                        include_html = include.read().decode('utf-8')
                        # SSI置換作業を実行
                        output_html = output_html.replace('<!--#include virtual="/' + include_path + '" -->', include_html)
                    except ClientError:
                        pass
            

            input_bucket.put_object(output_key, output_html)

    except Exception as e:
        logger.info(e)
        raise e