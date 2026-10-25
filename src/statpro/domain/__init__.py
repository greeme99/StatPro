"""Domain contracts shared by StatPro analysis adapters."""

from statpro.domain.data import (
    DataColumn,
    DatasetSnapshot,
    DataType,
    WorksheetSnapshot,
    create_worksheet,
    import_csv_bytes,
    import_csv_dataset,
    replace_worksheet_cell,
)
from statpro.domain.errors import AnalysisInputError
from statpro.domain.models import ResultBundle
from statpro.domain.schema import result_bundle_schema

__all__ = [
    "AnalysisInputError",
    "DataColumn",
    "DataType",
    "DatasetSnapshot",
    "ResultBundle",
    "WorksheetSnapshot",
    "create_worksheet",
    "import_csv_bytes",
    "import_csv_dataset",
    "replace_worksheet_cell",
    "result_bundle_schema",
]
