
# Health check monitor

This is a API health check monitor written in Python which takes the list of endpoint configuration from a JSON file, and runs the health check for each endpoint on a separate thread.
It also alerts the user via email when the ```resend_notification_interval``` threshold is crossed. AWS SES is used for sending emails.


How to run the code:
```
$ .\venv\Scripts\activate
$ pip install -r requirements.txt
$ py main.py
```
