from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from uuid import uuid4
from datetime import datetime
import enum

db = SQLAlchemy()
ma = Marshmallow()

class TranscriptionStatus(enum.Enum):
    pending = 0
    completed = 1
    error = 10

class VoiceMemo(db.Model):

    @classmethod
    def create(cls,     name, file_ext):
        return cls(name, datetime.utcnow(), str(uuid4()) + file_ext, 
                        TranscriptionStatus.pending, transcription = None)

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime)
    file_name = db.Column(db.String(64))
    status = db.Column(db.Enum(TranscriptionStatus))
    transcription = db.Column(db.Text())

    def __init__(self, name, created_at, file_name, status, transcription):
        self.name = name
        self.created_at = created_at
        self.file_name = file_name
        self.status = status
        self.transcription = transcription

    @property
    def file_guid(self):
        return self.file_name.split('.')[0]

class VoiceMemoSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'created_at', 'file_name', 'transcription')