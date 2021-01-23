import boto3
import pandas as pd
from sqlalchemy.orm import sessionmaker
from api.api import app, celery
from api.models import db, TranscriptionStatus, VoiceMemo

transcribe_client = boto3.client('transcribe')

@celery.task(name='transcription_polling')
def transcription_polling():
    print('transcription job started')

    with app.app_context():
        pending_transcriptions = VoiceMemo.query.filter(VoiceMemo.status == TranscriptionStatus.pending).all()
        print(f'{len(pending_transcriptions)} pending transcriptions...')
        if not pending_transcriptions:
            return

        for memo in pending_transcriptions:
            transcription = transcribe_client.get_transcription_job(TranscriptionJobName=f'VoiceMemo_{memo.file_guid}')
            if transcription['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                memo.transcription = pd.read_json(transcription['TranscriptionJob']['Transcript']['TranscriptFileUri'])['results'][1][0]['transcript']
                memo.status = TranscriptionStatus.completed
            elif transcription['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
                memo.status = TranscriptionStatus.error

        db.session.commit()