
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


from fdk import response

from datetime import datetime, date
from base64 import b64encode, b64decode

from oci.config import from_file
from oci.ai_anomaly_detection.models import *
from oci.ai_anomaly_detection.anomaly_detection_client import AnomalyDetectionClient

from oci.ai_anomaly_detection.models.create_project_details import CreateProjectDetails
from oci.ai_anomaly_detection.models.create_data_asset_details import CreateDataAssetDetails
from oci.ai_anomaly_detection.models.data_source_details import DataSourceDetails
from oci.ai_anomaly_detection.models.data_source_details_object_storage import DataSourceDetailsObjectStorage

from oci.ai_anomaly_detection.models.create_model_details import CreateModelDetails
from oci.ai_anomaly_detection.models.model_training_details import ModelTrainingDetails

from oci.ai_anomaly_detection.models.data_item import DataItem
from oci.ai_anomaly_detection.models.detection_result_item import DetectionResultItem
from oci.ai_anomaly_detection.models.inline_detect_anomalies_request import InlineDetectAnomaliesRequest


 ### Anomaly Detection ###

configfile = 'config'
modelid = 'ocid1.aianomalydetectionmodel.oc1.iad.amaaaaaay5l3z3yan45sm3cykwmiprvchapu4heu32iaxrl4wcau543wufta'
svc_endpoint = 'https://anomalydetection.aiservice.us-ashburn-1.oci.oraclecloud.com'
namespace = 'apaccpt01'
bucket_name = 'pi_ai_anomaly_detection'
compartment_id = 'ocid1.compartment.oc1..aaaaaaaaezxuhazglgc4ybhpde43uoiifwitlezypdvnhn6xqro6nomw7neq'
config = from_file(configfile)
ad_client = AnomalyDetectionClient(config, service_endpoint=svc_endpoint)
payloadData=[]
signalNames = ["machineid","timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5","anomaly"]
col=["temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]
outputdict={}
    # df=pd.read_csv('anomaly_test_data.csv')


def handler(ctx, data: io.BytesIO = None):

    ociMessageEndpoint = "https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com"
    ociStreamOcid = "ocid1.stream.oc1.iad.amaaaaaay5l3z3yayeorzxlmzhnvcj2fvfnexvqgoq5r2w4ezpjht7mhk3na"
    config = oci.config.from_file("config", "DEFAULT")


    # config = oci.config.from_file(ociConfigFilePath, ociProfileName)
    stream_client = oci.streaming.StreamClient(
        config, service_endpoint=ociMessageEndpoint)

    # A cursor can be created as part of a consumer group.
    # Committed offsets are managed for the group, and partitions
    # are dynamically balanced amongst consumers in the group.
    group_cursor = get_cursor_by_group(
        stream_client, ociStreamOcid, "example-group", "example-instance-1")
    simple_message_loop(stream_client, ociStreamOcid, group_cursor)



   

def get_cursor_by_group(sc, sid, group_name, instance_name):
    print(" Creating a cursor for group {}, instance {}".format(
        group_name, instance_name))
    cursor_details = oci.streaming.models.CreateGroupCursorDetails(group_name=group_name, instance_name=instance_name,
                                                                   type=oci.streaming.models.
                                                                   CreateGroupCursorDetails.TYPE_LATEST,
                                                                   commit_on_get=True)
    response = sc.create_group_cursor(sid, cursor_details)
    return response.data.value


def simple_message_loop(client, stream_id, initial_cursor):
    cursor = initial_cursor
    
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=100)
        # No messages to process. return.
        if not get_response.data:
            return
        # Process the messages 
        print(" Read {} messages".format(len(get_response.data)))
        #print(get_response.data)

        for message in get_response.data:
            
            #print(b64decode(message.value).decode('utf-8'))
            base64_string = ""
            base64_string = message.value
            base64_bytes = base64_string.encode("utf-8")
            
            sample_string_bytes = base64.b64decode(base64_bytes)
            sample_string = sample_string_bytes.decode("utf-8")
           
            
            inputdata = []
            reader = sample_string.split(',')
            inputdata = [ reader[0].replace('\'', '') ,reader[1].replace('\'', '') , float(reader[2]), float(reader[3]), float(reader[4]), float(reader[5]), float(reader[6]), float(reader[7]), float(reader[8]), float(reader[9]), float(reader[10]), float(reader[11]), int(reader[12])]

            

            print(inputdata)


            testdata=pd.read_csv("oci://"+bucket_name+"/anomaly_test_data.csv", storage_options = {"config": configfile})
            anomalypoint=pd.read_csv("oci://"+bucket_name+"/anomalies.csv", storage_options = {"config": configfile})
            anomalypoint['lookup']=anomalypoint['timestamp'].apply(lambda x:x[:19])
            anomalypoint.columns=['timestamp', 'sensor',
                'actualvalue', 'expectedvalue','anomalies.anomalyScore', 'score',
                'lookup']
            for ix,row in testdata[15:].iterrows():
                temp=pd.DataFrame([row])
                temp=t.melt(id_vars=["timestamp"], var_name="sensor", value_name="value")
                temp['lookup']=t['timestamp'].apply(lambda x:x[:19])
                temp1=t.merge(anomalypoint[['lookup','sensor','expectedvalue']],on=['lookup','sensor'],how='left')
                temp1['expectedvalue']=temp1.apply(lambda x:x['value'] if pd.isnull(x['expectedvalue']) else x['expectedvalue'],axis=1)
                temp['value_s']=np.round(temp['value'],4).map(str)
                temp['expectedvalue_s']=np.round(temp['expectedvalue'],4).map(str)
                temp['insertscript']=temp.apply(lambda x:"'"+x['lookup']+"','"+x['sensor']+"',"+x['value_s']+","+x['expectedvalue_s'],axis=1)
                ins='insert all into PPANOMALYDS7 values '
                for ix,row in temp.iterrows():
                    ins=ins+'('+row['insertscript']+') into PPANOMALYDS7 values'
                ins=ins[:-24]+' select 1 from dual'
                dbschema='admin'
                dbpwd='Autonomous14#'
                dbsqlurl = 'https://wwjfteltaqsqcy9-adsadw.adb.us-ashburn-1.oraclecloudapps.com/ords/admin/_/sql'
                headers = {"Content-Type": "application/sql"}
                auth=(dbschema, dbpwd)
                r = requests.post(dbsqlurl, auth=auth, headers=headers, data=ins)
                time.sleep(1)
          
          
        # get_messages is a throttled method; clients should retrieve sufficiently large message
        # batches, as to avoid too many http requests.
        time.sleep(1)
        # use the next-cursor for iteration
        cursor = get_response.headers["opc-next-cursor"]
