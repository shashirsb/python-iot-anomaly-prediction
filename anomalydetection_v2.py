# !pip install pandas
# !pip install ocifs
#deploy

import oci
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, date
import requests

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

config = from_file(configfile)

ad_client=AnomalyDetectionClient(config,service_endpoint=svc_endpoint)

testdata=pd.read_csv('anomaly_test_data.csv')
historicaldata=testdata[:21]

payloadData=[]
signalNames = ["machineid","timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5","anomaly"]
col=["temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]
inputdata=['Machine1']


#read historical data

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

ins=''
temp1=pd.DataFrame()
li_anomalies_dbentry=[]
temp=historicaldata[-1:][["timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]].melt(id_vars=["timestamp"], var_name="sensor", value_name="value")
temp['timestamp']=temp['timestamp'].apply(lambda x:x[:19])
print(t)
if len(detect_res.data.detection_results)>0:
    for rec in detect_res.data.detection_results:
        if rec.timestamp.replace(tzinfo=None)==t:
            print('Anomaly in Present T')
            if historicaldata[-10:]['anomaly'].sum() > 0:
                print('red flag')
            else:
                print('one time off')           
            for point in rec.anomalies:
                li_anomalies_dbentry.append([point.signal_name,point.estimated_value])
            temp1=pd.DataFrame(li_anomalies_dbentry,columns=['sensor','expectedvalue'])
            historicaldata.iloc[-1,historicaldata.columns.get_loc('anomaly')]=1

        else:
            print('Anomalies in Present T minus')
else:
    print('0 anomalies')

temp=historicaldata[-1:][["timestamp","temperature_1", "temperature_2", "temperature_3", "temperature_4", "temperature_5", "pressure_1", "pressure_2", "pressure_3", "pressure_4", "pressure_5"]].melt(id_vars=["timestamp"], var_name="sensor", value_name="value")
temp['timestamp']=temp['timestamp'].apply(lambda x:x[:19])
if len(temp1)>0:
    print('temp1')
    temp=temp.merge(temp1,on='sensor',how='left')
    temp['expectedvalue']=temp.apply(lambda x:x['value'] if pd.isnull(x['expectedvalue']) else x['expectedvalue'],axis=1)
else:
    temp['expectedvalue']=temp['value']
temp.rename(columns={'timestamp':'lookup'},inplace=True)
temp['value_s']=np.round(temp['value'],4).map(str)
temp['expectedvalue_s']=np.round(temp['expectedvalue'],4).map(str)
temp['insertscript']=temp.apply(lambda x:"'"+x['lookup']+"','"+x['sensor']+"',"+x['value_s']+","+x['expectedvalue_s'],axis=1)
ins='insert all into PPANOMALYDS5 values '
for ix,row in temp.iterrows():
    ins=ins+'('+row['insertscript']+') into PPANOMALYDS5 values'
ins=ins[:-24]+' select 1 from dual'
dbschema='admin'
dbpwd='Autonomous14#'
dbsqlurl = 'https://wwjfteltaqsqcy9-adsadw.adb.us-ashburn-1.oraclecloudapps.com/ords/admin/_/sql'
headers = {"Content-Type": "application/sql"}
auth=(dbschema, dbpwd)
r = requests.post(dbsqlurl, auth=auth, headers=headers, data=ins)
historicaldata.to_csv('oci://'+bucket_name+'/historicaldata.csv',index=False,storage_options = {"config": configfile})