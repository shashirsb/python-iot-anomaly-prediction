
# Copyright (c) 2016, 2021, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

##########################################################################
# inline_key_value_extraction_demo.py
#
# Supports Python 3
##########################################################################
# Info:
# Inline Key Value extraction Processor Job creation using OCI AI Document Understanding service.
#
##########################################################################
# Application Command line(no parameter needed)
# python inline_key_value_extraction_demo.py
##########################################################################

"""
This python script provides an example of how to use OCI Document Understanding Service key value extraction feature.

The configuration file used by service clients will be sourced from the default location (~/.oci/config) and the
CONFIG_PROFILE profile will be used.

The sample attempts extract key fields from an inline invoice document.
Successful run of this sample will create job results under object storage configured under output_location variable
"""
import oci
import uuid
import io
import json
import logging
import oci
import time
import requests
import base64
import pandas as pd
import numpy as np
import csv
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

# Setup basic variables
# Auth Config
# CONFIG_PROFILE = "DEFAULT"
# config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)


config = oci.config.from_file('config', "DEFAULT")


# Compartment where processor job will be created (required)
COMPARTMENT_ID = 'ocid1.compartment.oc1..aaaaaaaaflrsdacnlx6r7mertlzkpjqgrsbyjlln2rqmgrussoj4nd2lgqza'


def extract_key_value(file_base64):

    # sample document
    key_value_extraction_sample_string = file_base64
    # with open("resources/"+file, "rb") as document_file:
    #     key_value_extraction_sample_string = base64.b64encode(document_file.read()).decode('utf-8')

    def create_processor_job_callback(times_called, response):
        print("Waiting for processor lifecycle state to go into succeeded state:", response.data)

    aiservicedocument_client = oci.ai_document.AIServiceDocumentClientCompositeOperations(
        oci.ai_document.AIServiceDocumentClient(config=config))

    # Document Key-Value extraction Feature
    key_value_extraction_feature = oci.ai_document.models.DocumentKeyValueExtractionFeature()

    # Setup the output location where processor job results will be created
    output_location = oci.ai_document.models.OutputLocation()
    output_location.namespace_name = "bm3n5p8nor1r"  # e.g. "axk2tfhlrens"
    output_location.bucket_name = "ekyc-bucket"  # e.g "output"
    output_location.prefix = "demo"  # e.g "demo"

    # Create a processor_job for invoice key_value_extraction feature.
    # Note: If you want to use another key value extraction feature, set document_type to "RECEIPT" "PASSPORT" or "DRIVER_ID". If you have a mix of document types, you can remove document_type
    create_processor_job_details_key_value_extraction = oci.ai_document.models.CreateProcessorJobDetails(
        display_name=str(uuid.uuid4()),
        compartment_id=COMPARTMENT_ID,
        input_location=oci.ai_document.models.InlineDocumentContent(
            data=key_value_extraction_sample_string),
        output_location=output_location,
        processor_config=oci.ai_document.models.GeneralProcessorConfig(features=[key_value_extraction_feature],
                                                                       document_type="INVOICE"))

    print("Calling create_processor with create_processor_job_details_key_value_extraction:",
          create_processor_job_details_key_value_extraction)
    create_processor_response = aiservicedocument_client.create_processor_job_and_wait_for_state(
        create_processor_job_details=create_processor_job_details_key_value_extraction,
        wait_for_states=[
            oci.ai_document.models.ProcessorJob.LIFECYCLE_STATE_SUCCEEDED],
        waiter_kwargs={"wait_callback": create_processor_job_callback})

    print("processor call succeeded with status: {} and request_id: {}.".format(
        create_processor_response.status, create_processor_response.request_id))
    processor_job: oci.ai_document.models.ProcessorJob = create_processor_response.data
    print("create_processor_job_details_key_value_extraction response: ")

    print("Getting defaultObject.json from the output_location")
    object_storage_client = oci.object_storage.ObjectStorageClient(
        config=config)
    get_object_response = object_storage_client.get_object(namespace_name=output_location.namespace_name,
                                                           bucket_name=output_location.bucket_name,
                                                           object_name="{}/{}/_/results/defaultObject.json".format(
                                                               output_location.prefix, processor_job.id))

    import json
    import re

    # Assuming the JSON is stored in a variable called 'data'
    data = json.loads(get_object_response.data.content.decode())

    # Extracting lines text
    lines_text = [line['text'] for line in data['pages'][0]['lines']]

    # Finding the VendorTaxId
    vendor_tax_id = None
    for line in lines_text:
        match = re.search(r'\b[A-Za-z0-9]{15}\b', line)
        if match:
            vendor_tax_id = match.group()
            break

    # Finding the line containing the word "DLF"
    dlf_line = next((line for line in lines_text if "DLF" in line), None)

    # Extracting documentFields fieldLabel name
    field_label_names = [field['fieldLabel']['name']
                         for field in data['pages'][0]['documentFields']]

    # Extracting fieldValue text for KEY_VALUE fields
    key_value_texts = [field['fieldValue']['text'] for field in data['pages']
                       [0]['documentFields'] if field['fieldType'] == 'KEY_VALUE']

    # Extracting fieldValue text for LINE_ITEM_GROUP fields
    line_item_texts = [item['fieldValue']['text'] for field in data['pages'][0]['documentFields']
                       if field['fieldType'] == 'LINE_ITEM_GROUP' for item in field['fieldValue']['items']]

    # Creating a dictionary to store the extracted information
    extracted_info = {
        "line_text": lines_text,
        "key_value": dict(zip(field_label_names, key_value_texts)),
        "line_items": line_item_texts,
        "entity": "found" if dlf_line else "not found",
        "entity_value": dlf_line if dlf_line else "",
        "gst": vendor_tax_id
    }

    # Converting the dictionary to a JSON string
    json_output = json.dumps(extracted_info, indent=4)

    # Printing the JSON string
    print(json_output)

    # return str(get_object_response.data.content.decode())
    return str(json_output)


# Add a route for the POST request with file upload
@app.route('/extract', methods=['POST'])
def extract():
    file = request.files['file']
    if file:
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        return extract_key_value(file_base64)
    else:
        return 'No file uploaded.'


if __name__ == '__main__':
    app.run(port=5000)
