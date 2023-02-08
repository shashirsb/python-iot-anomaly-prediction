
import io
import json
import logging
import oci
import time
import requests
import base64
import pandas as pd
import numpy as np


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
print('line -------------------- 1a')
config = from_file(configfile)
ad_client = AnomalyDetectionClient(config, service_endpoint=svc_endpoint)
payloadData=[]
signalNames = ["machineid","timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5","anomaly"]
col=["temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]
outputdict={}
    # df=pd.read_csv('anomaly_test_data.csv')


def handler(ctx, data: io.BytesIO = None):

    ociMessageEndpoint = "https://cell-1.streaming.us-ashburn-1.oci.oraclecloud.com"
    ociStreamOcid = "ocid1.stream.oc1.iad.amaaaaaay5l3z3yanvjrsg74zxrpfymoomjmdtoedo5bnn4te6wdhy6hsmka"
    config = oci.config.from_file("config", "DEFAULT")

    print('line -------------------- func.py--1b')

    # config = oci.config.from_file(ociConfigFilePath, ociProfileName)
    stream_client = oci.streaming.StreamClient(
        config, service_endpoint=ociMessageEndpoint)

    # A cursor can be created as part of a consumer group.
    # Committed offsets are managed for the group, and partitions
    # are dynamically balanced amongst consumers in the group.
    group_cursor = get_cursor_by_group(
        stream_client, ociStreamOcid, "example-group", "example-instance-1")
    simple_message_loop(stream_client, ociStreamOcid, group_cursor)

    #    try:
    #         body = json.loads(data.getvalue())
    #         name = body.get("name")
    #     except (Exception, ValueError) as ex:
    #         logging.getLogger().info('error parsing json payload: ' + str(ex))

    #     logging.getLogger().info("Inside Python Hello World function")
    #     return response.Response(
    #         ctx, response_data=json.dumps(
    #             {"message": "Hello {0}".format(name)}),
    #         headers={"Content-Type": "application/json"}
    # )


   

def get_cursor_by_group(sc, sid, group_name, instance_name):
    print(" Creating a cursor for group {}, instance {}".format(
        group_name, instance_name))
    cursor_details = oci.streaming.models.CreateGroupCursorDetails(group_name=group_name, instance_name=instance_name,
                                                                   type=oci.streaming.models.
                                                                   CreateGroupCursorDetails.TYPE_TRIM_HORIZON,
                                                                   commit_on_get=True)
    response = sc.create_group_cursor(sid, cursor_details)
    return response.data.value


def simple_message_loop(client, stream_id, initial_cursor):
    cursor = initial_cursor
    print('line -------------------- func.py--1c')
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=100)
        # No messages to process. return.
        if not get_response.data:
            return
        # Process the messages 
        print(" Read {} messages".format(len(get_response.data)))
        #print(get_response.data)

        for message in get_response.data:
            inputdata=['Machine2','2019-01-07T21:37:02Z', -0.799584669679329, -1.6622950856002754,
       -2.5713350176048646, -3.667976951202916, -1.9241455114801511,
       -0.9752628709707616, -1.8615682557702289, 0.4649194526022965,
       0.2561157490030738, -1.128104113585569, 0]
            print("-------------------1a")
            print("-------------------1a")
            print("-------------------1a")
            print("-------------------1a")
            print("-------------------1ccc")
            #print(b64decode(message.value).decode('utf-8'))
            base64_string = message.value
            base64_bytes = base64_string.encode("utf-8")
            
            sample_string_bytes = base64.b64decode(base64_bytes)
            sample_string = sample_string_bytes.decode("utf-8")
            print(sample_string)
        

            print("-------------------1cccc")
            print("-------------------1a")
            # if message.key is None:
            #     key = "Null"
            # else:
            #     key = b64decode(message.key.encode()).decode()
            # print("{}: {}".format(key,
            #                       b64decode(message.value.encode()).decode()))
            historicaldata = pd.read_csv("oci://"+bucket_name+"/historicaldata.csv", storage_options = {"config": configfile})

            historicaldata=pd.concat([historicaldata,pd.DataFrame(data=[inputdata],columns=signalNames)])
       
            # retain last T to T-21 rows
            svcpayload=[]
            payload=historicaldata[-21:]

            for index,row in payload.iterrows():
                timestamp = datetime.strptime(row['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                t=timestamp
                values = list(row[col])
                dItem = DataItem(timestamp=timestamp, values=values)
                svcpayload.append(dItem)
                
            inline = InlineDetectAnomaliesRequest( model_id=modelid,  request_type="INLINE", signal_names=col, data=svcpayload)
            detect_res = ad_client.detect_anomalies(detect_anomalies_details=inline)


            li_anomalies=[]
            li_hist_anomalies=[]

            if len(detect_res.data.detection_results)>0:
                # check if T is anomaly
                for rec in detect_res.data.detection_results:
                    if rec.timestamp.replace(tzinfo=None)==t:
                        print('T is anomaly')
                        
                        if historicaldata[-10:]['anomaly'].sum() > 0:
                            print('red flag')
                            for val in detect_res.data.detection_results:
                                for val1 in val.anomalies:
                                    anomalyjson={'actual_value':val1.actual_value,'estimated_value':val1.estimated_value,'signal_name':val1.signal_name}
                                    li_anomalies.append(anomalyjson)
                            
                            for ix,row in historicaldata[historicaldata['anomaly']==1][-10:].iterrows():
                                anomalyjson={'pastincidents_time':row['timestamp']}
                                li_hist_anomalies.append(anomalyjson)
                            
                            outputdict={'time':val.timestamp,'anomalies':li_anomalies,'anomalytype':'warning','historicalval':li_hist_anomalies}
                        else:
                            print('one time off')
                            for val in detect_res.data.detection_results:
                                for val1 in val.anomalies:
                                    print(val1)
                                    anomalyjson={'actual_value':val1.actual_value,'estimated_value':val1.estimated_value,'signal_name':val1.signal_name}
                                    li_anomalies.append(anomalyjson)
                            outputdict={'time':val.timestamp,'anomalies':li_anomalies,'anomalytype':'warning','historicalval':li_hist_anomalies}
                        
                        
                        historicaldata.iloc[-1,historicaldata.columns.get_loc('anomaly')]=1
                    else:
                        print('No anomaly')
                
            historicaldata.to_csv('oci://'+bucket_name+'/historicaldata.csv',index=False,storage_options = {"config": configfile})


        # get_messages is a throttled method; clients should retrieve sufficiently large message
        # batches, as to avoid too many http requests.
        time.sleep(1)
        # use the next-cursor for iteration
        cursor = get_response.headers["opc-next-cursor"]
