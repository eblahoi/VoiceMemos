VoiceMemos
=========
This repository contains a VoiceMemo application referenced in my [blog](https://inspidev.com/2021/02/10/voicememos-on-aws-part-0-amazon-transcribe/).

The application is built with Flask, Celery and React to showcase an Amazon Transcribe service in action.

Quick setup
--------------

1. Clone the repository
2. Create S3 bucket
3. Create virtual env and install the dependencies for api and front-end
4. Setup environment variables for flask and celery. Example:
    - FLASK_APP=api/api.py
    - FLASK_ENV=development
    - DATABASE_URI=sqlite:///db.db
    - BROKER_URI=sqla+sqlite:///db.db
    - S3_BUCKET_NAME=inspidev-voicememos
5. Run flask, celery worker, celery beat, react