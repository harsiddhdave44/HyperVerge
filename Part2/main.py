import requests
import time
import threading
import logging
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError


class HealthCheckSystem:
    def __init__(self, config):
        self.config = config
        self.ses_client = boto3.client(
            'ses', region_name='us-east-2', aws_access_key_id='AKIARAU2UJCVNU2TQPVU', aws_secret_access_key='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')
        logging.basicConfig(filename='healthcheck.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

    def check_api(self, endpoints):
        # print(f"{url} Health Check: ")
        retries = 0
        while True:
            try:
                response = requests.request(
                    method=endpoints['method'], url=endpoints['url'], headers=endpoints['headers'])
                if response.status_code == 200:
                    logging.info(f"{endpoints['url']} Health Check: Pass")
                    retries = 0
                # print("#", end=" ")
                else:
                    retries += 1
                    logging.warning(
                        f"{endpoints['url']} Health Check: Fail (Retries: {retries})")
                    # print(endpoints['retries'])
                # print("x", end=" ")
                # print(f"Health check for {url} is failing")
                # continue
            except requests.exceptions.ConnectionError as e:
                retries += 1
                logging.error(
                    f"{endpoints['url']} Health Check: Error (Retries: {retries})")
                # print(endpoints['retries'])

                # print("x", end=" ")
                # print(f"Health check for {url} is failing")
                # continue

            if retries >= endpoints['retries']:
                print(f"Health check for {endpoints['url']} is failing")
            if retries % endpoints['resend_notification_interval'] == 0:
                self.send_email_notification(
                    endpoints['url'], endpoints['notify_email'])
                print("Resend notification via email")
                logging.error(
                    f"{endpoints['url']} Health Check: Error (Retries: {retries})\t Email notification sent")
            time.sleep(endpoint['check_interval'])

    def send_email_notification(self, url, notify_email):
        try:
            response = self.ses_client.send_email(
                Destination={
                    'ToAddresses': [notify_email],
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': "UTF-8",
                            'Data': f"The health check for {url} has failed. Please check the logs for more details.",
                        },
                    },
                    'Subject': {
                        'Charset': "UTF-8",
                        'Data': "API Health Check Failure",
                    },
                },
                Source="harsiddhdave44@outlook.com",
            )
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error sending email: {error}")


if __name__ == "__main__":
    # config = {
    #     'endpoints': [
    #         {
    #             'url': 'https://www.googlefail.co.in',
    #             'method': 'GET',
    #             'headers': {'Content-Type': 'application/json'},
    #             'check_interval': 60,  # seconds
    #             'retries': 3
    #         },
    #         {
    #             'url': 'https://www.youtubefail.com',
    #             'method': 'GET',
    #             'headers': {'Content-Type': 'application/json'},
    #             'check_interval': 60,  # seconds
    #             'retries': 3
    #         }
    #     ]
    # }
    config = []
    with open("endpoints.json", "r") as endpoints:
        config = json.load(endpoints)
    system = HealthCheckSystem(config)

    threads = []
    for endpoint in config['endpoints']:
        # print("")
        t = threading.Thread(target=system.check_api,
                             args=(endpoint,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
