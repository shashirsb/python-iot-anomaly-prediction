# !pip install pandas
# !pip install ocifs


import oci
import time
import json
import pandas as pd
import numpy as np

from datetime import datetime, date

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

configfile='config'

modelid='ocid1.aianomalydetectionmodel.oc1.iad.amaaaaaay5l3z3yan45sm3cykwmiprvchapu4heu32iaxrl4wcau543wufta'

svc_endpoint='https://anomalydetection.aiservice.us-ashburn-1.oci.oraclecloud.com'

namespace='apaccpt01'

bucket_name='pi_ai_anomaly_detection'

compartment_id = 'ocid1.compartment.oc1..aaaaaaaaezxuhazglgc4ybhpde43uoiifwitlezypdvnhn6xqro6nomw7neq'

print('line -------------------- 40')

config = from_file(configfile)


ad_client=AnomalyDetectionClient(config,service_endpoint=svc_endpoint)

# df=pd.read_csv('anomaly_test_data.csv')

payloadData=[]
signalNames = ["machineid","timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5","anomaly"]
col=["temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]
inputdata=['Machine1','2019-01-07T21:29:06Z', -0.799584669679329, -1.6622950856002754,
       -2.5713350176048646, -3.667976951202916, -1.9241455114801511,
       -0.9752628709707616, -1.8615682557702289, 0.4649194526022965,
       0.2561157490030738, -1.128104113585569, 0]
outputdict={}

# sample input data ['2019-01-07T21:21:10Z', -0.1427905888871324, -1.0470312022076451,
#         -1.1998935176672367, 1.7342866588566317, 0.6703094411821944,
#         -0.544271660891241, -4.269196261800262, -1.4225641947108985,
#         -2.002714329034521, 0.7536581234164882]

#read historical data

historicaldata = pd.read_csv("oci://"+bucket_name+"/historicaldata.csv", storage_options = {"config": configfile})

historicaldata=pd.concat([historicaldata,pd.DataFrame(data=[inputdata],columns=signalNames)])
print('line -------------------- 66')
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


# json.dumps(outputdict,default=str)