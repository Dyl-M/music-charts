"""ETL pipeline stages.

Exports:
    Base classes:
        - PipelineStage: Abstract base for pipeline stages
        - Pipeline: Pipeline orchestrator

    Observer pattern:
        - EventType: Enum of pipeline event types
        - PipelineEvent: Immutable event data class
        - PipelineObserver: Abstract observer interface
        - Observable: Mixin for observable objects
        - ConsoleObserver: Console logging observer
        - FileObserver: File logging observer
        - ProgressBarObserver: Progress bar observer
        - MetricsObserver: Metrics collection observer

    Pipeline stages:
        - ExtractionStage: MusicBee → Songstats ID resolution
        - EnrichmentStage: Fetch platform statistics
        - RankingStage: Compute power rankings

    Orchestration:
        - PipelineOrchestrator: Coordinates full pipeline execution
"""

# Local
from msc.pipeline.base import Pipeline, PipelineStage
from msc.pipeline.enrich import EnrichmentStage
from msc.pipeline.extract import ExtractionStage
from msc.pipeline.observer import EventType, Observable, PipelineEvent, PipelineObserver
from msc.pipeline.observers import (
    ConsoleObserver,
    FileObserver,
    MetricsObserver,
    ProgressBarObserver,
)
from msc.pipeline.orchestrator import PipelineOrchestrator
from msc.pipeline.rank import RankingStage

__all__ = [
    # Base classes
    "Pipeline",
    "PipelineStage",
    # Observer pattern
    "EventType",
    "PipelineEvent",
    "PipelineObserver",
    "Observable",
    "ConsoleObserver",
    "FileObserver",
    "ProgressBarObserver",
    "MetricsObserver",
    # Pipeline stages
    "ExtractionStage",
    "EnrichmentStage",
    "RankingStage",
    # Orchestration
    "PipelineOrchestrator",
]
