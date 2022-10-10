import logging
from pathlib import Path
from typing import List, Optional

import boto3
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box
from shapely.affinity import scale

from codem import resources


class UnsupportedFileType(Exception):
    """File type not supported"""


AOI_BUCKET = "codem-aoi"
REGISTERED_AOI_BUCKET = "codem-aoi-registered"
FOUNDATION_BUCKET = "codem-foundation"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def get_dsm_bounds(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:
    with rasterio.open(aoi_path) as dsm:
        src_bounds = box(*dsm.bounds)
        src_crs = dsm.crs
    src_buffered = scale(src_bounds, xfact=buffer_factor, yfact=buffer_factor)
    wgs84_buffered = transform_bounds(src_crs, {"init": "EPSG:4326"}, *src_buffered.bounds)
    return list(wgs84_buffered)


def get_mesh_bounds(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:
    # https://trimsh.org/trimesh.parent.html?highlight=box#trimesh.parent.Geometry3D.bounding_box
    # https://trimsh.org/trimesh.parent.html?highlight=box#trimesh.parent.Geometry3D.bounding_box_oriented
    ...


def get_pointcloud_bounds(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:
    ...


def handler(event, context):
    records = event["Records"]
    if len(records) > 1:
        raise ValueError("Only a single AOI file at a time can be uploaded")
    else:
        record = records[0]

    # download aoi file
    bucket = record["s3"]["bucket"]["name"]
    if bucket != AOI_BUCKET:
        raise ValueError("Incorrect AOI bucket name")

    aoi_file = record["s3"]["object"]["key"]
    aoi_download_path = f"/tmp/{aoi_file}"
    s3_client.download_file(AOI_BUCKET, aoi_file, aoi_download_path)
    logger.info(f"Downloaded aoi file from s3: {aoi_file}")

    # get rough aoi location in wgs84
    ext = Path(aoi_download_path).suffix
    if ext in resources.dsm_filetypes:
        bounds = get_dsm_bounds(aoi_download_path)
    elif ext in resources.mesh_filetypes:
        bounds = get_mesh_bounds(aoi_download_path)
    elif ext in resources.pcloud_filetypes:
        bounds = get_pointcloud_bounds(aoi_download_path)
    else:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")

    # query Planetary Computer USGS 3DEP for foundation




    # download and merge the 3DEP data



    # save foundation data to foundation bucket



    # that's it. the co-register step will find the foundation data
    # future would be to pass the file name to the next step function

