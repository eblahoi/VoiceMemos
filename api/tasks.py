import boto3
import urllib.request
import json
from api.api import app, celery
from api.models import db, TranscriptionStatus, VoiceMemo

transcribe_client = boto3.client('transcribe')

@celery.task(name='transcription_polling')
def transcription_polling():
    print('transcription job started')

    with app.app_context():
        #get all voice memos with pending transcriptions
        pending_transcriptions = VoiceMemo.query.filter(VoiceMemo.status == TranscriptionStatus.pending).all()
        print(f'{len(pending_transcriptions)} pending transcriptions...')
        if not pending_transcriptions:
            return

        for memo in pending_transcriptions:
            #get a transcription job using a memo file guid
            transcription = transcribe_client.get_transcription_job(TranscriptionJobName=f'VoiceMemo_{memo.file_guid}')

            #check transcription job status
            if transcription['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                #download transcription
                with urllib.request.urlopen(transcription['TranscriptionJob']['Transcript']['TranscriptFileUri']) as url:
                    transcription_json = json.loads(url.read())
                    memo.transcription = transcription_json['results']['transcripts'][0]['transcript']
                    memo.status = TranscriptionStatus.completed
            elif transcription['TranscriptionJob']['TranscriptionJobStatus'] == 'FAILED':
                memo.status = TranscriptionStatus.error

        db.session.commit()