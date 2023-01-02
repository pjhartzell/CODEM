import dataclasses
import logging
from pathlib import Path

import boto3

import codem


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def run_codem(foundation, aoi):
    codem_run_config = codem.CodemRunConfig(foundation, aoi)
    config = dataclasses.asdict(codem_run_config)
    fnd_obj, aoi_obj = codem.preprocess(config)
    fnd_obj.prep()
    aoi_obj.prep()
    dsm_reg = codem.coarse_registration(fnd_obj, aoi_obj, config)
    icp_reg = codem.fine_registration(fnd_obj, aoi_obj, dsm_reg, config)
    reg_file = codem.apply_registration(fnd_obj, aoi_obj, icp_reg, config)
    return reg_file


def handler(event, context):
    logger.info(event)

    aoi_bucket = event["aoi_bucket"]
    aoi_filename = event["aoi_filename"]
    foundation_filename = event["foundation_filename"]
    result_bucket = event["result_bucket"]
    result_directory = event["result_directory"]

    # download aoi file
    aoi_download_path = f"/tmp/{aoi_filename}"
    s3_client.download_file(aoi_bucket, aoi_filename, aoi_download_path)
    logger.info(f"Downloaded aoi file from s3: {aoi_filename}")

    # download foundation file
    foundation_s3_path = f"{result_directory}/{foundation_filename}"
    foundation_download_path = f"/tmp/{foundation_filename}"
    s3_client.download_file(
        result_bucket, foundation_s3_path, foundation_download_path
    )
    logger.info(f"Downloaded foundation file from s3: {foundation_s3_path}")

    # register aoi image to foundation image
    registered_aoi_file_path = run_codem(foundation_download_path, aoi_download_path)
    logger.info("Registered AOI to Foundation")

    # upload registration results
    local_result_directory = Path(registered_aoi_file_path).parent
    for result_file in local_result_directory.glob("*"):
        local_path = str(result_file)
        s3_upload_path = f"{result_directory}/{result_file.name}"
        s3_client.upload_file(
            local_path,
            result_bucket,
            s3_upload_path,
        )
        logger.info(f"Uploaded registration result file to s3: {s3_upload_path}")

    logger.info("Registration complete.")
