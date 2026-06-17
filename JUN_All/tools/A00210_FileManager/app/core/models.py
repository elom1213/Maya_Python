# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - core data models (UI/DCC 비의존)
#
# Maya 씬 파일 1개에 대한 작업 기록(메타데이터) 모델.
# JSON 직렬화/역직렬화 헬퍼를 포함한다.

from dataclasses import dataclass, field, asdict


@dataclass
class LogEntry:
    """작업자가 남긴 기록 1줄."""

    timestamp: str = ""   # ISO8601 문자열 (UI 에서 생성)
    author: str = ""
    note: str = ""

    @staticmethod
    def from_dict(data):
        return LogEntry(
            timestamp=data.get("timestamp", ""),
            author=data.get("author", ""),
            note=data.get("note", ""),
        )


@dataclass
class FileRecord:
    """Maya 파일 1개의 기록. key 는 프로젝트 루트 기준 상대경로."""

    key: str = ""                 # 예: "chars/charA_rig.mb"
    file_name: str = ""
    author: str = ""              # 대표 작업자
    logs: list = field(default_factory=list)   # list[LogEntry]
    thumb_rel: str = ""           # 스토어 내 썸네일 상대경로 ("" 면 없음)
    updated_by: str = ""
    updated_at: str = ""

    def to_dict(self):
        data = asdict(self)
        # asdict 가 LogEntry 도 dict 로 변환한다.
        return data

    @staticmethod
    def from_dict(data):
        record = FileRecord(
            key=data.get("key", ""),
            file_name=data.get("file_name", ""),
            author=data.get("author", ""),
            thumb_rel=data.get("thumb_rel", ""),
            updated_by=data.get("updated_by", ""),
            updated_at=data.get("updated_at", ""),
        )
        record.logs = [
            LogEntry.from_dict(item)
            for item in data.get("logs", [])
        ]
        return record
