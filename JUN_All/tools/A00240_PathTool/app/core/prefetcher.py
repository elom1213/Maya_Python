# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00240_PathTool - background folder prefetcher
#
# 구현은 Framework 로 승격됨(A00480_FileTool Maya 탭과 공유, v01.20). 기존 호출부
# (`from ..core.prefetcher import Prefetcher`) 가 그대로 동작하도록 re-export 만 남긴다.
from Framework.core.prefetcher import Prefetcher  # noqa: F401  (re-export)
