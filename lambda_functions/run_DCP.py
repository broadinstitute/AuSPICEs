import os
import sys
import boto3

sys.path.append("/tmp")


def run_setup(bucket_name, prefix, batch, config_dict, type="cellprofiler"):
    os.chdir("/tmp")
    if os.path.exists("/tmp/configAWS.py"):
        os.remove("/tmp/configAWS.py")
        print("removed previous config file")
    grab_batch_config(bucket_name, prefix, batch)
    import boto3_setup

    app_name = boto3_setup.setup(config_dict, type)
    return app_name


def run_cluster(bucket_name, prefix, batch, njobs, config_dict):
    os.chdir("/tmp")
    grab_fleet_file(bucket_name, prefix, batch)
    import boto3_setup

    boto3_setup.startCluster("configFleet.json", njobs, config_dict)


def grab_batch_config(bucket_name, prefix, batch):
    s3 = boto3.client("s3")
    our_config = prefix + "lambda/" + batch + "/configAWS.py"
    import botocore

    try:
        with open("/tmp/configAWS.py", "wb") as f:
            s3.download_fileobj(bucket_name, our_config, f)
    except botocore.exceptions.ClientError as error:
        print(
            f"Config files for this batch haven't been uploaded to S3. Upload them to {our_config}"
        )
        return


def grab_fleet_file(bucket_name, prefix, batch):
    s3 = boto3.client("s3")
    our_fleet = prefix + "lambda/" + batch + "/configFleet.json"
    try:
        with open("/tmp/configFleet.json", "wb") as f:
            s3.download_fileobj(bucket_name, our_fleet, f)
    except botocore.exceptions.ClientError as error:
        print("Error grabbing fleet file.")
        return


def setup_monitor(bucket, prefix, config_dict):
    import boto3_setup

    boto3_setup.create_sqs_alarms(config_dict)
    boto3_setup.upload_monitor(bucket, prefix, config_dict)
    boto3_setup.create_dashboard(config_dict)
