
import boto3
import logging
import os
import paramiko
import time
import uuid

from botocore.exceptions import ClientError
from datetime import datetime

logging.getLogger("paramiko").setLevel(logging.INFO)

BLUEPRINT = "ubuntu_16_04_1"
# BUILDID = "nano_1_2"
BUILDID = "medium_1_2"
# KEY_PAIR_NAME = "Default"
AVAILABILITY_ZONE = "ap-southeast-2"  # Sydney, AU
# AVAILABILITY_ZONE = "ap-southeast-2a"  # Sydney, AU
PEM_FILE = "/Users/hugh.saalmans/.aws/LightsailDefaultPrivateKey-ap-southeast-2.pem"
INSTANCE_NAME = "census_loader_instance_v2"
VPC_ID = "vpc-79da031c"


def main():
    full_start_time = datetime.now()

    proxies = passwords.proxies

    # get uuid based passwords
    password_array = str(uuid.uuid4()).split("-")
    admin_password = password_array[1] + password_array[4].upper() + password_array[0] + password_array[3].upper()
    password_array = str(uuid.uuid4()).split("-")
    readonly_password = password_array[3] + password_array[2].upper() + password_array[4] + password_array[0].upper()

    # get ec2 client (ignoring IAG's invalid SSL certificate)
    ec2_client = boto3.client('ec2', verify=False, region_name=AVAILABILITY_ZONE,
                              config=Config(proxies={"https": proxies["https"]}))

    # # get VPC ID
    # response_dict = ec2_client.describe_vpcs()
    # vpc_id = response_dict.get('Vpcs', [{}])[0].get('VpcId', '')
    # print(vpc_id)

    # get subnet ID
    subnet_id = None
    response_dict = ec2_client.describe_network_interfaces()
    for response in response_dict["NetworkInterfaces"]:
        if response["VpcId"] == VPC_ID:
            subnet_id = response["SubnetId"]

    # check if security group exists
    security_group_id = None
    response_dict = ec2_client.describe_security_groups()

    for response in response_dict["SecurityGroups"]:
        if response["GroupName"] == GROUP_NAME:
            security_group_id = response["GroupId"]
            # vpc_id = response["VpcId"]

    # create security group (if it doesn't exist)
    if security_group_id is None:
        response_dict = ec2_client.create_security_group(GroupName=GROUP_NAME,
                                                         Description='Opens port 5432 for Postgres database servers',
                                                         VpcId=VPC_ID)
        security_group_id = response_dict['GroupId']

        response_dict = ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 5432,
                 'ToPort': 5432,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ])
        logger.info("\tSecurity Group {0} ({1}) created in VPC {2}".format(GROUP_NAME, security_group_id, VPC_ID))
        logger.info("\t\t{0}".format(response_dict))
    else:
        logger.info("\tSecurity Group {0} ({1}) already exists in VPC {2}".format(GROUP_NAME, security_group_id, VPC_ID))

    # get ec2 service resources (ignoring IAG's invalid SSL certificate)
    ec2 = boto3.resource('ec2', verify=False, region_name=AVAILABILITY_ZONE,
                         config=Config(proxies={"https": proxies["https"]}))

    # create EC2 instance
    response_dict = ec2.create_instances(
        ImageId=AMI_ID,  # Ubuntu 16.04 LTS - see https://cloud-images.ubuntu.com/locator/ec2/
        MinCount=1,
        MaxCount=1,
        KeyName="loceng-key",
        InstanceType=BUILD_ID,
        SubnetId=subnet_id,
        SecurityGroupIds=[security_group_id],
        Placement={"AvailabilityZone": AVAILABILITY_ZONE + "c"},
        TagSpecifications=[
            {
                'ResourceType': "instance",
                'Tags': [
                    {
                        "Key": "Name",
                        "Value": "loceng test database"
                    },
                    {
                        "Key": "Owner",
                        "Value": "s57405"
                    },
                    {
                        "Key": "Purpose",
                        "Value": "Choice of Repairer testing"
                    },
                ]
            },
        ],
        DryRun=False
    )
    logger.info("EC2 instance created")
    logger.info("\t\t{0}".format(response_dict))









    # wait until instance is running
    instance_dict = get_lightsail_instance(lightsail_client, INSTANCE_NAME)

    while instance_dict["state"]["name"] != 'running':
        logger.info('\t\tWaiting 15 seconds... instance is %s' % instance_dict["state"]["name"])
        time.sleep(15)
        instance_dict = get_lightsail_instance(lightsail_client, INSTANCE_NAME)

        # open the Postgres port on the instance
        response_dict = lightsail_client.open_instance_public_ports(
            portInfo={
                'fromPort': 5432,
                'toPort': 5432,
                'protocol': "tcp"
            },
            instanceName=INSTANCE_NAME
        )
        logger.info("\t\t{0}".format(response_dict))

    logger.info('\t\tWaiting 30 seconds... instance is booting')
    time.sleep(30)

    instance_ip = instance_dict["publicIpAddress"]
    cpu_count = instance_dict["hardware"]["cpuCount"]
    logger.info("\t\tPublic IP address: {0}".format(instance_ip))

    # create SSH client
    key = paramiko.RSAKey.from_private_key_file(PEM_FILE)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname=instance_ip, username="ubuntu", pkey=key)

    logger.info("Connected to new server via SSH : {0}".format(datetime.now() - full_start_time))
    logger.info("")

    # run each bash command
    bash_file = os.path.abspath(__file__).replace(".py", ".sh")
    bash_commands = open(bash_file, 'r').read().split("\n")

    for cmd in bash_commands:
        if cmd[:1] != "#" and cmd[:1].strip(" ") != "":  # ignore comments and blank lines
            # replace text with passwords if required
            if "<postgres-password>" in cmd:
                cmd = cmd.replace("<postgres-password>", admin_password)
            if "<rouser-password>" in cmd:
                cmd = cmd.replace("<rouser-password>", readonly_password)

            run_ssh_command(ssh_client, cmd, admin_password)

    # data and code loaded - run the thing using gunicorn!
    cmd = "sudo gunicorn -w {0} -D --pythonpath ~/git/census-loader/web/ -b 0.0.0.0:80 single_server:app"\
        .format(cpu_count * 2)
    run_ssh_command(ssh_client, cmd, admin_password)

    # TODO: Put NGINX in front of gunicorn as a reverse proxy"

    ssh_client.close()

    logger.info("Public IP address : {}".format(instance_ip))
    logger.info("")
    logger.info("Admin password    : {}".format(admin_password))
    logger.info("Readonly password : {}".format(readonly_password))
    logger.info("")
    logger.info("Total time : : {0}".format(datetime.now() - full_start_time))
    logger.info("")
    return True


def get_lightsail_instance(lightsail_client, name):
    response = lightsail_client.get_instance(instanceName=name)

    return response["instance"]


def run_ssh_command(ssh_client, cmd, admin_password):
    start_time = datetime.now()
    logger.info("START : {0}".format(cmd))

    # run command
    # try:
    stdin, stdout, stderr = ssh_client.exec_command(cmd)

    # send Postgres user password when running pg_restore
    if "pg_restore" in cmd:
        stdin.write(admin_password + '\n')
        stdin.flush()

    # log everything

    # for line in stdin.read().splitlines():
    #     if line:
    #         logger.info(line)
    stdin.close()

    for line in stdout.read().splitlines():
        pass
        # if line:
        #     logger.info("\t\t{0}".format(line))
    stdout.close()

    for line in stderr.read().splitlines():
        if line:
            logger.info("\t\t{0}".format(line))
    stderr.close()

    logger.info("END   : {0} : {1}".format(cmd, datetime.now() - start_time))

    # except:
    #     logger.warning("FAILED! : {0} : {1}".format(cmd, datetime.now() - start_time))

    logger.info("")


if __name__ == '__main__':
    logger = logging.getLogger()

    # set logger
    log_file = os.path.abspath(__file__).replace(".py", ".log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(message)s",
                        datefmt="%m/%d/%Y %I:%M:%S %p")

    # setup logger to write to screen as well as writing to log file
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logger.info("")
    logger.info("Start ec2-build")

    if main():
        logger.info("Finished successfully!")
    else:
        logger.fatal("Something bad happened!")

    logger.info("")
    logger.info("-------------------------------------------------------------------------------")
