from dataclasses import dataclass
import os
from typing import Any, Dict, Optional


@dataclass
class CodemParameters:
    "Parses CODEM parameters from S3 bucket uploads and API POSTs"
    aoi_bucket: str
    aoi_file: str
    fnd_bucket: Optional[str] = None
    fnd_file: Optional[str] = None
    fnd_buffer_factor: float = float(os.environ.get("BUFFER_FACTOR"))
    min_resolution: Optional[float] = None
    solve_scale: Optional[bool] = None

    def from_bucket_upload(cls, message: Dict[str, Any]) -> "CodemParameters":
        return CodemParameters(
            aoi_bucket=message["s3"]["bucket"]["name"],
            aoi_file=message["s3"]["object"]["key"],
        )

    def from_api_post(cls, message: Dict[str, Any]) -> "CodemParameters":
        if message.get("fndBufferFactor", None) is not None:
            fnd_buffer_factor = message["fndBufferFactor"]
        return CodemParameters(
            aoi_bucket=message["aoiBucket"],
            aoi_file=message["aoiFile"],
            fnd_bucket=message.get("fndBucket", None),
            fnd_file=message.get("fndFile", None),
            fnd_buffer_factor=fnd_buffer_factor,
            min_resolution=message.get("codemMinResolution", None),
            solve_scale=message.get("codemSolveScale", None),
        )


def parse_message(message: Dict[str, Any]) -> CodemParameters:
    if message.get("Records", None):
        records = message["Records"]
        if len(records) > 1:
            raise ValueError(f"More than one ({len(records)}) file uploaded.")
        else:
            return CodemParameters.from_bucket_upload(records[0])
    else:
        return CodemParameters.from_api_post(message)
