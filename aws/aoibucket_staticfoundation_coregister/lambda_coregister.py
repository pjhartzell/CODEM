import dataclasses
import logging
import os
import time

import boto3

import codem

AOI_BUCKET = "codem-aoi"
REGISTERED_AOI_BUCKET = "codem-aoi-registered"
FOUNDATION_BUCKET = "codem-foundation"

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

    # download foundation file
    response = s3_client.list_objects(Bucket=FOUNDATION_BUCKET)
    files = [file["Key"] for file in response.get("Contents")]
    if len(files) > 1:
        raise ValueError(
            f"Only a single Foundation file is allowed in the {FOUNDATION_BUCKET} bucket"
        )

    foundation_file = files[0]
    foundation_download_path = f"/tmp/{foundation_file}"
    s3_client.download_file(
        FOUNDATION_BUCKET, foundation_file, foundation_download_path
    )
    logger.info(f"Downloaded foundation file from s3: {foundation_file}")

    # register aoi image to foundation image
    registered_aoi_file_path = run_codem(foundation_download_path, aoi_download_path)
    registered_aoi_filename = os.path.basename(registered_aoi_file_path)
    result_directory = (
        f"{os.path.splitext(os.path.basename(aoi_file))[0]}-"
        f"{time.strftime('%Y%m%d_%H%M%S')}"
    )
    registered_aoi_s3_path = f"{result_directory}/{registered_aoi_filename}"
    logger.info("Registered AOI to Foundation")

    # upload registered aoi
    # ADD TIMESTAMP TO DIRECTORY
    s3_client.upload_file(
        registered_aoi_file_path,
        REGISTERED_AOI_BUCKET,
        registered_aoi_s3_path,
    )
    logger.info(f"Uploaded registered aoi file to s3: {registered_aoi_s3_path}")
