from datetime import timedelta
import celery
from flask import Flask, json, request, jsonify
from pathlib import Path
from werkzeug.exceptions import HTTPException
from api.models import db, ma, VoiceMemo, VoiceMemoSchema
import os
import boto3
from celery import Celery

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
app.config['broker_url'] = os.environ.get('BROKER_URI')
app.config['S3_BUCKET_NAME'] = os.environ.get('S3_BUCKET_NAME')
app.config['beat_schedule'] = {
    'transcription_polling': {
        'task': 'transcription_polling',
        'schedule': timedelta(seconds=60)
    }
}

db.init_app(app)
ma.init_app(app)
transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')

celery = Celery(
    app.import_name,
    broker=app.config['broker_url'],
    include=['api.tasks']
)
celery.conf.update(app.config)

voicememo_schema = VoiceMemoSchema()
voicememos_schema = VoiceMemoSchema(many=True)

with app.app_context():
    db.create_all()

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        'code': e.code,
        'name': e.name,
        'description': e.description
    })
    response.content_type = 'application/json'
    return response

@app.route('/memos', methods=['GET'])
def get_memos():
    all_memos = VoiceMemo.query.order_by(VoiceMemo.created_at.desc()).all()
    result = voicememos_schema.dump(all_memos)
    return jsonify(result)

@app.route('/memos', methods=['POST'])
def create_memo():
    file = request.files['file']
    file_extension = Path(file.filename).suffix.lower()
    new_memo = VoiceMemo.create(request.form['name'].strip(), file_extension)

    #upload file to S3
    s3_client.upload_fileobj(file.stream, app.config['S3_BUCKET_NAME'], new_memo.file_name)

    #start transcription job
    file_uri = f's3://{app.config["S3_BUCKET_NAME"]}/{new_memo.file_name}'
    transcribe_client.start_transcription_job(
        TranscriptionJobName=f'VoiceMemo_{new_memo.file_guid}',
        Media={'MediaFileUri': file_uri},
        LanguageCode = 'en-US'
    )

    db.session.add(new_memo)
    db.session.commit()

    return jsonify(voicememo_schema.dump(new_memo))

@app.route('/memos/<id>', methods=['DELETE'])
def delete_memo(id):
    memo = VoiceMemo.query.get_or_404(id)

    #delete recording file
    s3_client.delete_object(Bucket=app.config["S3_BUCKET_NAME"], Key=memo.file_name)
    #delete transcription job
    transcribe_client.delete_transcription_job(
        TranscriptionJobName=f'VoiceMemo_{memo.file_guid}')

    #delete db record
    db.session.delete(memo)
    db.session.commit()

    return '', 204

if __name__ == '__main__':
    app.run(debug=True)