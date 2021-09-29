import boto3
import botocore
import shutil
from pe2loaddata.__main__ import headless as pe2loaddata
import yaml

s3 = boto3.client("s3")


def lambda_handler(event, lambda_context):
    fullplate = event["trigger"]["plate"]
    plate = fullplate.split("__")[0]
    project_name = event["project_name"]
    batch = event["batch"]
    bucket = event["bucket"]
    channeldict = event["channeldict"]

    # Create channel map
    if channeldict == "Standard_1BF":
        channelmap = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
        }
    elif channeldict == "Standard_3BF":
        channelmap = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
            "Brightfield H": "OrigBrightfield_H",
            "Brightfield L": "OrigBrightfield_L",
        }
    else:
        if type(channeldict) is not dict:
            print(
                "In metadata: enter string for existing map into channeldict enter new map as dictionary."
            )
            return
        else:
            channelmap = channeldict

    # Load and edit config file with channel map
    shutil.copy("./config.yml", "/tmp/config.yml")
    config_file = "/tmp/config.yml"
    with open(config_file, "r") as fd:
        config = yaml.load(fd, Loader=yaml.BaseLoader)
    config["channels"] = channelmap
    with open(config_file, "w") as fd:
        yaml.dump(config, fd, Dumper=yaml.Dumper)

    # Trigger pe2loaddata
    output = f"/tmp/load_data.csv"
    index_directory = f"s3://{bucket}/projects/{project_name}/{batch}/images/{plate}"
    index_file = f"s3://{bucket}/projects/{project_name}/{batch}/images/{fullplate}/Images/Index.idx.xml"
    illum_directory = f"projects/{project_name}/{batch}/illum/{plate}"
    illum_output = f"/tmp/load_data_with_illum.csv"
    sub_string_out = "projects"
    sub_string_in = "/home/ubuntu/bucket/projects"

    pe2loaddata(
        config_file,
        output,
        index_directory=index_directory,
        index_file=index_file,
        illum=True,
        illum_directory=illum_directory,
        plate_id=plate,
        illum_output=illum_output,
        sub_string_out=sub_string_out,
        sub_string_in=sub_string_in,
        search_subdirectories=True,
    )

    # Upload .csvs to S3
    output_on_bucket_name = (
        f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data.csv"
    )
    illum_output_on_bucket_name = f"projects/{project_name}/workspace/load_data_csv/{batch}/{plate}/load_data_with_illum.csv"
    with open(output, "rb") as a:
        s3.put_object(Body=a, Bucket=bucket, Key=output_on_bucket_name)
    with open(illum_output, "rb") as a:
        s3.put_object(Body=a, Bucket=bucket, Key=illum_output_on_bucket_name)
