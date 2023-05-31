import requests
import time
import threading
import logging
import json
import boto3
from dotenv import load_dotenv
from os import getenv
from botocore.exceptions import BotoCoreError, ClientError


class HealthCheckSystem:
    def __init__(self, config):
        self.config = config
        load_dotenv()
        # boto3 client instantiation
        self.ses_client = boto3.client(
            'ses', region_name='us-east-2', aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=getenv('AWS_ACCESS_SECRET_KEY'))
        logging.basicConfig(filename='healthcheck.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')

    def check_api(self, endpoints):
        retries = 0
        while True:
            try:
                response = requests.request(
                    method=endpoints['method'], url=endpoints['url'], headers=endpoints['headers'])
                if response.status_code == 200:
                    logging.info(f"{endpoints['url']} Health Check: Pass")
                    retries = 0
                else:
                    retries += 1
                    logging.warning(
                        f"{endpoints['url']} Health Check: Fail (Retries: {retries})")
            except requests.exceptions.RequestException as e:
                retries += 1
                logging.warning(
                    f"{endpoints['url']} Health Check: Error (Retries: {retries})")

            # If the number of retries exceeds the given retry count, print the message to log
            if retries >= endpoints['retries']:
                print(f"Health check for {endpoints['url']} is failing")
                logging.error(
                    f"{endpoints['url']} Health Check Failed: Error (Retries: {retries})")
            # If the number of retries exceeds the `resend_notificataion_interval`, send an alert to the email using AWS SES
            if retries % endpoints['resend_notification_interval'] == 0:
                self.send_email_notification(
                    endpoints['url'], endpoints['notify_email'])
                logging.error(
                    f"{endpoints['url']} Health Check: Error (Retries: {retries})\t Email notification sent")
            # Sleep added for health check interval
            time.sleep(endpoints['check_interval'])

    def send_email_notification(self, url, notify_email):
        try:
            # Both the Source and Destination emails must be verified if in the SES sandbox
            self.ses_client.send_email(
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
    config = []

    try:
        with open("endpoints.json", "r") as endpoints:
            config = json.load(endpoints)
        system = HealthCheckSystem(config)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        logging.error(f"Error reading config file: {error}")

    threads = []
    # Run health check for each endpoint in a separate thread
    for endpoint in config['endpoints']:
        t = threading.Thread(target=system.check_api,
                             args=(endpoint,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
