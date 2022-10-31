import logging
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

import boto3
import planetary_computer as pc
import rasterio
import rasterio.mask
import rasterio.merge
import requests
from codem import resources
from pystac_client import Client
from rasterio.warp import (Resampling, calculate_default_transform, reproject,
                           transform_bounds)
from shapely.affinity import scale
from shapely.geometry import box, mapping


class UnsupportedFileType(Exception):
    """File type not supported"""


AOI_BUCKET = "codem-aoi"
REGISTERED_AOI_BUCKET = "codem-aoi-registered"
FOUNDATION_BUCKET = "codem-foundation"
STAC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def dsm_foundation_bbox(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:
    with rasterio.open(aoi_path) as dsm:
        src_bounds = box(*dsm.bounds)
        src_crs = dsm.crs
    src_buffered = scale(src_bounds, xfact=buffer_factor, yfact=buffer_factor)
    wgs84_buffered = transform_bounds(src_crs, {"init": "EPSG:4326"}, *src_buffered.bounds)
    return list(wgs84_buffered)


# def mesh_foundation_bbox(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:
    # https://trimsh.org/trimesh.parent.html?highlight=box#trimesh.parent.Geometry3D.bounding_box
    # https://trimsh.org/trimesh.parent.html?highlight=box#trimesh.parent.Geometry3D.bounding_box_oriented


# def pointcloud_foundation_bbox(aoi_path: str, buffer_factor: Optional[float] = 2) -> List[float]:


def download_dsms(urls: List[str], destination: str) -> List[str]:
    local_paths = []
    for url in urls:
        download_path = Path(destination, Path(url).name)
        signed_url = pc.sign(url)
        response = requests.get(signed_url, stream=True)
        with open(download_path, "wb") as fout:
            for chunk in response.iter_content(chunk_size=4096):
                fout.write(chunk)
        local_paths.append(download_path)
    return local_paths


def make_consistent(dsm_paths: List[str], destination: str) -> List[str]:
    """Handles differing projections, but not differing spatial resolutions"""
    crss = []
    for dsm_path in dsm_paths:
        with rasterio.open(dsm_path) as src:
            crss.append(src.crs)

    crs_count = Counter(crss)
    dst_crs = crs_count.most_common(1)[0][0]

    consistent_dsm_paths = []
    for dsm_path in dsm_paths:
        with rasterio.open(dsm_path) as src:
            if src.crs != dst_crs:
                consistent_path = dsm_path.parent / f"{dsm_path.stem}_reprojected.tif"
                transform, width, height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds
                )
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': dst_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                with rasterio.open(consistent_path, 'w', **kwargs) as dst:
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=rasterio.band(dst, 1),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest
                    )
                consistent_dsm_paths.append(consistent_path)
            else:
                consistent_dsm_paths.append(dsm_path)
    return consistent_dsm_paths


def merge_dsms(dsm_paths: List[str], destination: str) -> str:
    open_dsms = [rasterio.open(dsm_path) for dsm_path in dsm_paths]
    merged, transform = rasterio.merge.merge(open_dsms)

    out_meta = open_dsms[0].meta.copy()
    for open_dsm in open_dsms:
        open_dsm.close()
    out_meta.update({
        "driver": "GTiff",
        "height": merged.shape[1],
        "width": merged.shape[2],
        "transform": transform
    })

    merged_path = Path(destination, "merged.tif")
    with rasterio.open(merged_path, "w", **out_meta) as dst:
        dst.write(merged)

    return merged_path


def crop_dsm(path: str, bbox: Tuple[float], destination: str) -> str:
    with rasterio.open(path) as src:
        proj_src_crs = rasterio.CRS.from_epsg(4326)
        proj_dst_crs = src.crs
        projected_box = mapping(box(*transform_bounds(proj_src_crs, proj_dst_crs, *bbox)))
        cropped_image, cropped_transform = rasterio.mask.mask(src, [projected_box], crop=True)
        cropped_meta = src.meta

    cropped_meta.update({
        "driver": "GTiff",
        "height": cropped_image.shape[1],
        "width": cropped_image.shape[2],
        "transform": cropped_transform}
    )

    cropped_path = Path(destination, "cropped.tif")
    with rasterio.open(cropped_path, "w", **cropped_meta) as dst:
        dst.write(cropped_image)

    return cropped_path


def handler(event, context):
    records = event["Records"]
    if len(records) > 1:
        raise ValueError("Only a single AOI file at a time can be uploaded")
    else:
        record = records[0]

    # download aoi file
    aoi_file = record["s3"]["object"]["key"]
    aoi_download_path = f"/tmp/{aoi_file}"
    s3_client.download_file(AOI_BUCKET, aoi_file, aoi_download_path)
    logger.info(f"Downloaded aoi file from s3: {aoi_file}")

    # get foundation bbox (buffered rough aoi bbox) in wgs84
    ext = Path(aoi_download_path).suffix
    if ext in resources.dsm_filetypes:
        foundation_bbox = dsm_foundation_bbox(aoi_download_path)
    elif ext in resources.mesh_filetypes:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    elif ext in resources.pcloud_filetypes:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    else:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    logger.info("Foundation bounding box estimated from AOI georeferencing data.")

    # pull USGS 3DEP DSM from the Planetarcy Computer for foundation
    catalog = Client.open(STAC_API)
    query = catalog.search(
        collections=["3dep-lidar-dsm"],
        bbox=foundation_bbox
    )

    items = list(query.get_items())
    dsm_urls = [i.assets["data"].href for i in items]

    with TemporaryDirectory() as tmp_dir:
        dsm_paths = download_dsms(dsm_urls, tmp_dir)
        logger.info("Foundation DSMs downloaded")

        if len(dsm_paths) > 1:
            consistent_dsm_paths = make_consistent(dsm_paths, tmp_dir)
            merged_dsm_path = merge_dsms(consistent_dsm_paths, tmp_dir)
            logger.info("Foundation DSMs merged.")

        cropped_dsm_path = crop_dsm(merged_dsm_path, foundation_bbox, tmp_dir)
        logger.info("Foundation DSM cropped to foundation bounding box.")

        # upload registered aoi
        foundation_dsm_s3_path = (
            f"{Path(aoi_file).stem}/{Path(aoi_file).stem}-foundation.tif"
        )
        s3_client.upload_file(
            cropped_dsm_path,
            FOUNDATION_BUCKET,
            foundation_dsm_s3_path,
        )
        logger.info(f"Uploaded foundation DSM file to s3: {foundation_dsm_s3_path}")
