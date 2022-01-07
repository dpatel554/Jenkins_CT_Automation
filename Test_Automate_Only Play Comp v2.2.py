# ------------------------------------------------------------------------------------------------------------------------
# Example: Automatic Test Execution Using CloudTest API
# Author : Kumar Venkatasubramanian (kvenkata@akamai.com)
# version: 2.2
# ------------------------------------------------------------------------------------------------------------------------

# includes
import requests
import json
import sys
import time
import pandas as pd
import urllib
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ------------------------------------------------------------------------------------------------------------------------
# variables

# Environment
# ENV_NAME=''
# CTM_TENANT = 'CloudTest'
# ENV_ID= ''

# HOSTNAME = 'http://ec2-34-230-239-122.compute-1.amazonaws.com'
# API_TOKEN = '82129f6b-0be7-4aa7-8e73-5ee6a9dc2c17'
# COMPS_PATH = '<Get Composition Path/CompositionName'
# GRID_NAME = 'GridName'
# TENANT = 'Tenant name'


SLA_ERRORS = 5.0  # in numbers, example: 5.0 is 5%
CHECK_ERROR_DURATION = 300 # Value in seconds, Errors will be checked after 300 seconds

MAX_RETRY_COUNT = 60
MAX_RETRY_DELAY = 30  # Value in Seconds


# ------------------------------------------------------------------------------------------------------------------------
# Get CTM Authentication
data = {}
data['apiToken'] = API_TOKEN
data['tenant'] = CTM_TENANT

# Get Token
token_url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/RepositoryService/v1/Tokens'
header = ''
token=''
ctm_token=''
try:

    # Get token
    response = requests.put(token_url, json.dumps(data), headers={
                            'Content-Type': 'application/octet-stream'}, verify=False)
    ctm_token = str(response.json()['token'])
    header = {"Content-Type": "application/json", "X-Auth-Token": ctm_token}
    #print(response.text)
    print("INFO: 1.  CTM Authentication is success.")

except:
    sys.exit("ERROR: CTM - Environment access denied!")


time.sleep(5)
# ------------------------------------------------------------------------------------------------------------------------
# Get Environment Id
token_url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/RepositoryService/v1/Objects/testenvironment'
header = {"Content-Type":"application/json", "Authorization":"Bearer " + API_TOKEN, "X-Tenant-Name": CTM_TENANT}

try:
    # Get token
    response = requests.get(token_url, headers=header, verify=False)
    result_Objects = response.json()['objects']
    for env in result_Objects:
        if env['name'] == ENV_NAME:
            #print(env['name'] + '-->'+ str(env['id']))
            ENV_ID = str(env['id'])
    
    if (len(ENV_ID)<2):
            sys.exit(f"ERROR: Please check the environment name : {ENV_NAME}")
    
except:
    sys.exit(f"ERROR: Please check the environment name : {ENV_NAME}")

#Get Environment Info
try:
  
    header = {"Content-Type": "application/json", "X-Auth-Token": ctm_token}
    url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/CloudService/v1/environment/'+ ENV_ID
    results = requests.get(url, headers=header, verify=False)
    envState = results.json()['state']
    if (envState == "TERMINATED"):
        #Start the environment
        header = {"Content-Type":"application/json","X-Auth-Token":ctm_token}
        json_str = {"action" : "start"}
        url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/CloudService/v1/environment/' + ENV_ID + '/action'
        results = requests.post(url, json=json_str, headers=header, verify=False)
        #print(results.text)
      
      # Check status of the CT environment
        header = {"Content-Type": "application/json", "X-Auth-Token": ctm_token}
        url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/CloudService/v1/environment/'+ ENV_ID
        envState = ''

        for x in range(MAX_RETRY_COUNT):

            try:
                results = requests.get(url, headers=header, verify=False)
                envState = str(results.json()['state'])
                print("INFO:     Environment is " + envState + "...")

                if envState == "RUNNING":
               	    break

            except:
                print('ERROR: Unable to start the environment!')

         	# wait for next status in seconds
            time.sleep(MAX_RETRY_DELAY)

        if envState != "RUNNING":
        	sys.exit("ERROR: Please check the environment status in the CloudTest Manager!")
        else:
            print(f"INFO: 2.  CloudTest Environment {HOSTNAME} is ready!")
      
      
    elif (envState == "RUNNING"):
        print(f"INFO: 2.  CloudTest Environment {HOSTNAME} is ready!")
    else:
      sys.exit(f"ERROR: Unable to start the environment {ENV_NAME}. More info can be found in the CloudTest Manager")    
      
except:
    sys.exit(f"ERROR: Unable to start the environment {ENV_NAME}. More info can be found in the CloudTest Manager")    

time.sleep(5)

# ------------------------------------------------------------------------------------------------------------------------
# Authentication
data = {}
data['apiToken'] = API_TOKEN
data['tenant'] = TENANT

# Get Token
token_url = HOSTNAME+'/concerto/services/rest/RepositoryService/v1/Tokens'
results_url = HOSTNAME+'/concerto/services/rest/RepositoryService/v1/Objects/result'
header = ''
try:

    # Get token
    response = requests.put(token_url, json.dumps(data), headers={
                            'Content-Type': 'application/octet-stream'}, verify=False)
    token = str(response.json()['token'])
    header = {"Content-Type": "application/json", "X-Auth-Token": token}
    #print(response.text)
    print("INFO: 3.  Authentication is success.")

except:
    sys.exit("ERROR: " + HOSTNAME + " - Environment is not up and running...!")


time.sleep(10)


# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# Get Grid Id
url = HOSTNAME + '/concerto/services/rest/RepositoryService/v1/Objects/grid?name=' + GRID_NAME
results = requests.get(url, headers=header, verify=False)
#print(results.text)
print("INFO: 4.  Get Grid ID for '" + GRID_NAME + "'")

try:
    # Extract grid_id from the response
    grid_id = str(results.json()['objects'][0]['id'])
    #print('Grid ID : ' + grid_id)

except:
    sys.exit("ERROR: Unable to get the Grid ID!")


time.sleep(10)


# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# Start the grid
url = HOSTNAME + '/concerto/services/rest/CloudService/v1/grid/' + grid_id + '/action'
json_str = {"action": "start"}
try:
    results = requests.post(url, json=json_str, headers=header, verify=False)
    #print(results.text)
    print("INFO: 5.  Starting the Grid '" + GRID_NAME + "'.")

except:
    sys.exit("ERROR: Unable to start the Grid!")


# Check status of the grid
url = HOSTNAME + '/concerto/services/rest/CloudService/v1/grid/' + grid_id
grid_status_text = ""

for x in range(MAX_RETRY_COUNT):

    try:
        results = requests.get(url, headers=header, verify=False)
        #print(results.text)

        grid_status_text = str(results.json()['state'])
        print("INFO:     Grid is " + grid_status_text + "...")

        if grid_status_text == "CHECKED":
       	    break

    except:
        print('ERROR: Unable to get the status of the Grid!')

 	# wait for next status in seconds
    time.sleep(MAX_RETRY_DELAY)

if grid_status_text != "CHECKED":
	sys.exit("ERROR: Please check the status of Grid!")
else:
    print("INFO: 6.  Grid is ready")


time.sleep(10)


# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
#To Load the composition
json_str = {"compositionName": COMPS_PATH}
results_url = HOSTNAME + '/concerto/services/rest/composition/instances/v1?command=load'
instance_id = None
print("INFO: 7.  Loading the Compostition.")

try:
  results = requests.post(results_url, json=json_str,
                          headers=header, verify=False)
  #print(results.text)

  #Extract instance_id from the response
  instance_id = str(results.json()['instanceID'])
  #print("Instance Id: " + instance_id)


except:
    error_msg = str(results.json()['message'])
    sys.exit('ERROR: Load Composition - ' + error_msg + ' ' + COMPS_PATH)

#Stop if we don't have an active instance id
if instance_id is None:
	sys.exit("ERROR: Load Composition - No Active InstanceID Found!")
else:
    print("INFO: 8.  Compostition is Loaded.")

time.sleep(10)
# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
#Play an already loaded Composition
json_str = {"compositionName": COMPS_PATH}
results_url = HOSTNAME + '/concerto/services/rest/composition/instances/v1/' + instance_id + '?command=play'
results_id = None
instance_id = None

try:
    results = requests.put(results_url, json=json_str, headers=header, verify=False)
    instance_id = str(results.json()['instanceID'])
    #print(results.text)
    #print("Instance Id: " + instance_id)
    print("INFO: 9.  Ready to Play the composition '" + COMPS_PATH + "'")

except:
    error_msg = str(results.json()['message'])
    sys.exit('ERROR: An error occurred when try to play the composition ' + COMPS_PATH)


#Stop if we don't have an active instance id
if instance_id is None:
	sys.exit("ERROR: No Active InstanceID Found, Play Composition Failed!")


#Get Instance Status
PLAY = True
instance_state = None
time.sleep(MAX_RETRY_DELAY)
colHeader = True
while PLAY:
    url = HOSTNAME + '/concerto/services/rest/composition/instances/v1/' + instance_id
    results = requests.get(url, headers=header, verify=False)
    instance_state = str(results.json()['state'])
    print("INFO:     Composition " + instance_state + "...")
    #Break if Composition State="Unloaded"
    if instance_state == "Unloaded":
        break

    #Get active result id
    results_id = str(results.json()['resultid'])
    #print('Active results id: ' + results_id)

    #Get duration in seconds
    totalTime = int(results.json()['totalTime'])/1000

    if totalTime > CHECK_ERROR_DURATION:
        #Get clip-element groupBy=error
        url = HOSTNAME + '/concerto/services/rest/Results/v1/' + results_id + '/clip-element?elementType=message'
        results = requests.get(url, headers=header, verify=False)
        #print(results.text)
        totalCount = results.json()['elementTypes'][0]['metrics']['count']
        totalErrors = results.json()['elementTypes'][0]['metrics']['errors']
        errorPercentage = float(totalErrors/totalCount * 100)
        #print("Total Errors: {:.2f}".format(errorPercentage)+ '%')

        #Check the number of errors aginst the defined SLA
        if errorPercentage > SLA_ERRORS:
            PLAY = False

            #stop the composition
            results_url = HOSTNAME + '/concerto/services/rest/composition/instances/v1/' + instance_id + '?command=stop'
            results = requests.put(results_url, json=json_str, headers=header, verify=False)
            #print("INFO:     Composition is stopped.")

            url = HOSTNAME + '/concerto/services/rest/Results/v1/' + results_id + '/clip-element?groupBy=error'
            results = requests.get(url, headers=header, verify=False)
            #print(results.text)
            error_Info = str(results.json()['errors'])
            for item in (results.json()['errors']):
                for key, value in item.items():
                    if type(value) is list:
                        if (item['error'] != "No Error"):
                            if colHeader:
                                print("Total Errors: {:.2f}".format(errorPercentage) + '% which is greater than the defined SLA of ' + str(SLA_ERRORS) + '%')
                                colHeader = False
                            print(item['error'], '->', value[0]['metrics']['errors'])

    time.sleep(MAX_RETRY_DELAY)

print('INFO: 10.  Composition is stopped.')

time.sleep(10)
# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------
# Terminate the Grid
url = HOSTNAME + '/concerto/services/rest/CloudService/v1/grid/' + grid_id + '/action'
json_str = {"action": "terminate"}
try:
    results = requests.post(url, json=json_str, headers=header, verify=False)
    #print(results.text)
    print("INFO: 11.  Terminating the Grid " + GRID_NAME + "...")

except:
    sys.exit("ERROR: Unable to Start the Grid!")

print("INFO: 12. Grid is terminated.")

time.sleep(10)


# ------------------------------------------------------------------------------------------------------------------------

#Pull all results for the composition
header = {"Content-Type": "application/json", "X-Auth-Token": token}
url = HOSTNAME + '/concerto/services/rest/Results/v1?composition=' + urllib.parse.quote(COMPS_PATH)
results = requests.get(url, headers=header, verify=False)
print("INFO: 13. Getting Test Results...")
#print(results.text)

#Get the latest test resultID from the results
latest_result_id = str(results.json()['results'][0]['id'])
#print(latest_result_id)

#Get the result name
exportFileName = str(results.json()['results'][0]['name']) + '.csv'
#print(exportFileName)

#Get Metrics for a resultId
url = HOSTNAME + "/concerto/services/rest/Results/v1/" + latest_result_id + "/collection?percentile=90&percentile=95&percentile=99&groupBy=flattenedHierarchy"
indv_result = requests.get(url, headers=header, verify=False)
#print(indv_result.text)

final_list = []
for key, value in (indv_result.json().items()):
    for trans in value:
        if (trans['containerType'] == 'transaction'):
            ind_trans = trans['metrics']
            trans_name = trans['flattenedHierarchy'].split('/')[-1]  # Transaction name
            trans_count = ind_trans['totalResponseCount']
            trans_min = ind_trans['minResponseTime']
            # converting Milliseconds to Seconds
            t_min = format(float(trans_min/1000), ".2f")

            trans_avg = ind_trans['averageResponseTime']
            # converting Milliseconds to Seconds
            t_avg = format(float(trans_avg/1000), ".2f")

            trans_max = ind_trans['maxResponseTime']
            # converting Milliseconds to Seconds
            t_max = format(float(trans_max/1000), ".2f")

            trans_std = ind_trans['effectiveDurationStandardOfDeviation']
            # converting Milliseconds to Seconds
            t_std = format(float(trans_std/1000), ".2f")

            trans_percentiles = ind_trans['percentiles']
            # converting Milliseconds to Seconds
            t_percentile_90 = format(float(trans_percentiles[0]['value'])/1000, ".2f")
            # converting Milliseconds to Seconds
            t_percentile_95 = format(float(trans_percentiles[0]['value'])/1000, ".2f")
            # converting Milliseconds to Seconds
            t_percentile_99 = format(float(trans_percentiles[0]['value'])/1000, ".2f")

            final_list.append([trans_name, trans_count, t_min, t_avg, t_max, t_percentile_90, t_percentile_95, t_percentile_99, t_std])


#print(final_list)


df = pd.DataFrame(final_list)
df.rename(columns={0: 'Transaction',
                   1: 'Collections Completed',
                   2: 'Min Duration[s]',
                   3: 'Avg Duration[s]',
                   4: 'Max Duration[s]',
                   5: 'Standard Deviation[s]',
                   6: '90th Percentile[s]',
                   7: '95th Percentile[s]',
                   8: '99th Percentile[s]'}, inplace=True)

#df = df.pivot(index='Transaction')

df.to_csv(exportFileName, index=True, header=True)
print("INFO: 14. Results Exported to " + exportFileName)

# ------------------------------------------------------------------------------------------------------------------------

#Terminate the environment
header = {"Content-Type":"application/json","X-Auth-Token":ctm_token}
json_str = {"action" : "terminate"}
url = 'https://cloudtestmanager.soasta.com/concerto/services/rest/CloudService/v1/environment/' + ENV_ID + '/action'
results = requests.post(url, json=json_str, headers=header, verify=False)
print(f"INFO: 15. CloudTest Environment {ENV_NAME} is terminated! ")
print("All Done!")
