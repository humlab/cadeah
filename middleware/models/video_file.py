from enum import Enum, auto
from pathlib import Path

from flask import current_app
from flask_admin.contrib.sqla import ModelView
from flask_socketio import SocketIO
from loguru import logger
from marshmallow_enum import EnumField

from .. import admin
from ..config import Config
from ..services.fingerprint import extract_fingerprints
from . import db, ma


socketio = SocketIO(message_queue=Config.REDIS_URL)


class VideoFileType(Enum):
    QUERY = auto()
    REFERENCE = auto()

    @staticmethod
    def from_str(label: str):
        if label == 'QUERY':
            return VideoFileType.QUERY
        elif label == 'REFERENCE':
            return VideoFileType.REFERENCE
        else:
            expected_values = list(map(lambda ft: ft.name, VideoFileType))
            raise ValueError(
                f'Unexpected value for VideoFileType. Got={label}.'
                f' Expected={expected_values}'
            )


class VideoFileState(Enum):
    NOT_FINGERPRINTED = auto()
    FINGERPRINTED = auto()
    UPLOADED = auto()


class VideoFile(db.Model):  # type: ignore
    pk = db.Column(db.Integer(), primary_key=True)

    video_name = db.Column(db.String(), unique=True)
    display_name = db.Column(db.Unicode())

    # TODO: Add video_duration = db.Column(db.Float()) and
    # have computations have a FK to here
    file_path = db.Column(db.String())
    processing_state = db.Column(db.Enum(VideoFileState))
    file_type = db.Column(db.Enum(VideoFileType))

    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now(),
        onupdate=db.func.now(),
    )

    def __init__(
        self, file_path: Path, file_type: VideoFileType, display_name: str = ''
    ):
        self.video_name = file_path.name

        if display_name == '':
            self.display_name = self.video_name
        else:
            self.display_name = display_name

        self.file_path = str(file_path)
        self.processing_state = VideoFileState.NOT_FINGERPRINTED
        self.file_type = file_type

    def mark_as_fingerprinted(self):
        self.processing_state = VideoFileState.FINGERPRINTED

    def is_fingerprinted(self):
        return self.processing_state == VideoFileState.FINGERPRINTED

    @staticmethod
    def from_upload(file_path: Path, display_name: str = '') -> 'VideoFile':
        video_file = VideoFile(file_path, VideoFileType.QUERY, display_name)
        video_file.processing_state = VideoFileState.UPLOADED

        return video_file

    @staticmethod
    def from_archival_footage(file_path: Path, display_name: str = '') -> 'VideoFile':
        return VideoFile(file_path, VideoFileType.REFERENCE, display_name)

    def __repr__(self):
        return f'VideoFile={VideoFileSchema().dumps(self)}'


def after_insert(video_file):
    emit_event(video_file, 'video_file_added')

    file_path = video_file.file_path

    logger.info(
        f'Extracting fingerprints for "{file_path}" after insertion of "{video_file}""'  # noqa: E501
    )

    extract_job = current_app.extract_queue.enqueue(
        extract_fingerprints, file_path, job_timeout=6000
    )

    # Important to enqueue at front otherwise the UI is not notified until
    # the entire set of videos available at start-up has been processed.
    current_app.extract_queue.enqueue(
        mark_as_done, file_path, depends_on=extract_job, at_front=True
    )


def __mark_as_done__(file_path: Path):
    video_name = file_path.name
    logger.success(f'Marking "{video_name}" as fingerprinted')

    video_file = db.session.query(VideoFile).filter_by(video_name=video_name).first()
    video_file.mark_as_fingerprinted()
    db.session.commit()

    emit_event(video_file, 'video_file_fingerprinted')


def mark_as_done(file_path: str):
    __mark_as_done__(Path(file_path))


def emit_event(video_file: VideoFile, event_name: str):
    logger.trace(f'Emitting "{event_name}" for {str(video_file)}')
    socketio.emit(event_name, VideoFileSchema().dump(video_file))


admin.add_view(ModelView(VideoFile, db.session))


class VideoFileSchema(ma.ModelSchema):
    processing_state = EnumField(VideoFileState)
    file_type = EnumField(VideoFileType)

    class Meta:
        model = VideoFile
