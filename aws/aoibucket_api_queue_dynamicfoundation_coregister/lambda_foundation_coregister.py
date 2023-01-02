import logging
from pathlib import Path

import boto3
from utils import parse_message
from foundation import get_foundation

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handler(event, context):
    parameters = parse_message(event)

    aoi_path = f"/tmp/{parameters.aoi_file}"
    s3_client.download_file(
        parameters.aoi_bucket, parameters.aoi_file, aoi_path
    )
    logger.info(f"AOI downloaded: {parameters.aoi_file}")

    foundation_path = get_foundation(parameters, aoi_path)
    logger.info(f"Foundation downloaded: {foundation_path}")
    
    
    
    
    
    ext = Path(aoi_path).suffix
    if ext in resources.dsm_filetypes:
        foundation_bbox = dsm_foundation_bbox(aoi_path)
    elif ext in resources.mesh_filetypes:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    elif ext in resources.pcloud_filetypes:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    else:
        raise UnsupportedFileType(f"File type '{ext}' is not supportd.")
    logger.info("Foundation bounding box estimated from AOI metadata.")

    # pull USGS 3DEP DSM from the Planetary Computer for foundation
    catalog = Client.open(STAC_API)
    query = catalog.search(collections=["3dep-lidar-dsm"], bbox=foundation_bbox)

    items = list(query.get_items())
    dsm_urls = [i.assets["data"].href for i in items]
    logger.info(f"Planetary Computer USGS 3DEP query returned {len(dsm_urls)} items.")

    with TemporaryDirectory() as tmp_dir:
        dsm_paths = download_dsms(dsm_urls, tmp_dir)
        logger.info("Foundation DSMs downloaded")

        if len(dsm_paths) > 1:
            consistent_dsm_paths = make_consistent(dsm_paths, tmp_dir)
            merged_dsm_path = merge_dsms(consistent_dsm_paths, tmp_dir)
            logger.info("Foundation DSMs merged.")

        cropped_dsm_path = crop_dsm(merged_dsm_path, foundation_bbox, tmp_dir)
        logger.info("Foundation DSM cropped to foundation bounding box.")

        # upload foundation dsm
        foundation_filename = f"{Path(aoi_file).stem}-foundation.tif"
        foundation_directory = f"{Path(aoi_file).stem}-{time.strftime('%Y%m%d_%H%M%S')}"
        foundation_s3_path = f"{foundation_directory}/{foundation_filename}"
        s3_client.upload_file(
            cropped_dsm_path,
            FOUNDATION_BUCKET,
            foundation_s3_path,
        )
        logger.info(f"Uploaded foundation DSM file to s3: {foundation_s3_path}")
