import io
import json
import logging
import oci
import time
import requests
import base64
import sys



from datetime import datetime, date
from base64 import b64encode, b64decode

from oci.config import from_file


filename = sys.argv[1]


ociMessageEndpoint = "https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com"
ociStreamOcid = "ocid1.stream.oc1.iad.amaaaaaay5l3z3yanvjrsg74zxrpfymoomjmdtoedo5bnn4te6wdhy6hsmka"
config = oci.config.from_file("config", "DEFAULT")

print('line -------------------- func.py--1b')

# config = oci.config.from_file(ociConfigFilePath, ociProfileName)
stream_client = oci.streaming.StreamClient(
   config, service_endpoint=ociMessageEndpoint)


def publish_example_messages(client, stream_id):
    # Build up a PutMessagesDetails and publish some messages to the stream
    message_list = []

    # Open the file for reading
    with open(filename, 'r') as file:
        # Read each line of the file
        for line in file:      
            key = "iot".encode("utf-8")
            value = line.encode("utf-8")
            encoded_key = b64encode(key).decode()
            encoded_value = b64encode(value).decode()
            message_list.append(oci.streaming.models.PutMessagesDetailsEntry(key=encoded_key, value=encoded_value))

    print("Publishing {} messages to the stream {} ".format(len(message_list), stream_id))
    messages = oci.streaming.models.PutMessagesDetails(messages=message_list)
    put_message_result = client.put_messages(stream_id, messages)

publish_example_messages(stream_client, ociStreamOcid)