from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from msc.config.settings import Settings, get_settings
from msc.utils.logging import PipelineLogger

"""Abstract base class for ETL pipeline stages."""

# Type variables for input and output data types
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class PipelineStage(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all pipeline stages.

    Implements the ETL (Extract-Transform-Load) pattern with:
    - extract(): Load input data from source
    - transform(): Process and transform data
    - load(): Save output data to destination

    Type Parameters:
        InputT: Type of input data from extract()
        OutputT: Type of output data from transform()
    """

    def __init__(
            self,
            settings: Settings | None = None,
            input_path: Path | None = None,
            output_path: Path | None = None,
    ):
        """Initialize the pipeline stage.

        Args:
            settings: Application settings. Uses global settings if None.
            input_path: Override path for input data.
            output_path: Override path for output data.
        """
        self.settings = settings or get_settings()
        self.input_path = input_path
        self.output_path = output_path
        self.logger = PipelineLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Human-readable name for this pipeline stage."""
        raise NotImplementedError("Subclasses must implement stage_name property")

    @abstractmethod
    def extract(self) -> InputT:
        """Extract/load input data from source.

        Returns:
            Input data for transformation.
        """
        raise NotImplementedError("Subclasses must implement extract()")

    @abstractmethod
    def transform(self, data: InputT) -> OutputT:
        """Transform input data to output format.

        Args:
            data: Input data from extract().

        Returns:
            Transformed output data.
        """
        raise NotImplementedError("Subclasses must implement transform()")

    @abstractmethod
    def load(self, data: OutputT) -> None:
        """Load/save output data to destination.

        Args:
            data: Transformed data from transform().
        """
        raise NotImplementedError("Subclasses must implement load()")

    def run(self) -> OutputT:
        """Execute the full ETL pipeline.

        Runs extract → transform → load in sequence with logging.

        Returns:
            The transformed output data.
        """
        self.logger.info(f"Starting {self.stage_name}")

        self.logger.info("Extracting data...")
        raw_data = self.extract()
        self.logger.info("Extraction complete")

        self.logger.info("Transforming data...")
        transformed_data = self.transform(raw_data)
        self.logger.info("Transformation complete")

        self.logger.info("Loading data...")
        self.load(transformed_data)
        self.logger.info("Load complete")

        self.logger.info(f"Completed {self.stage_name}")
        return transformed_data

    # TODO: Remove skipcq after implementing validation logic in subclasses
    def validate_input(self, data: InputT) -> bool:  # skipcq: PYL-R6301
        """Validate input data before transformation.

        Override in subclasses for custom validation logic.

        Args:
            data: Input data to validate.

        Returns:
            True if data is valid.
        """
        return True

    # TODO: Remove skipcq after implementing validation logic in subclasses
    def validate_output(self, data: OutputT) -> bool:  # skipcq: PYL-R6301
        """Validate output data before loading.

        Override in subclasses for custom validation logic.

        Args:
            data: Output data to validate.

        Returns:
            True if data is valid.
        """
        return True


class Pipeline:
    """Orchestrator for running multiple pipeline stages in sequence."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the pipeline orchestrator.

        Args:
            settings: Application settings. Uses global settings if None.
        """
        self.settings = settings or get_settings()
        self.logger = PipelineLogger("Pipeline")
        self._stages: list[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        """Add a stage to the pipeline.

        Args:
            stage: Pipeline stage to add.

        Returns:
            Self for method chaining.
        """
        self._stages.append(stage)
        return self

    def run(self, stages: list[str] | None = None) -> dict[str, object]:
        """Run the pipeline stages.

        Args:
            stages: List of stage names to run. Runs all if None.

        Returns:
            Dictionary mapping stage names to their output data.
        """
        results: dict[str, object] = {}

        for stage in self._stages:
            if stages is not None and stage.stage_name not in stages:
                self.logger.info(f"Skipping {stage.stage_name}")
                continue

            try:
                result = stage.run()
                results[stage.stage_name] = result
            except Exception as e:
                self.logger.error(f"Stage {stage.stage_name} failed: {e}")
                raise

        return results
