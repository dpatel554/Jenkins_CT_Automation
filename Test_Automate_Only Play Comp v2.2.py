# ------------------------------------------------------------------------------------------------------------------------
# Example: Automatic Test Execution Using CloudTest API
# Author : Kumar Venkatasubramanian (kvenkata@akamai.com)
# version: 2.2
# ------------------------------------------------------------------------------------------------------------------------

# includes
import os
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

HOSTNAME = os.getenv("HOSTNAME")
API_TOKEN = os.getenv("API_TOKEN")
COMPS_PATH = os.getenv("COMPS_PATH")
# GRID_NAME = 'GridName'
TENANT = os.getenv("TENANT")


SLA_ERRORS = 5.0  # in numbers, example: 5.0 is 5%
CHECK_ERROR_DURATION = 300 # Value in seconds, Errors will be checked after 300 seconds

MAX_RETRY_COUNT = 60
MAX_RETRY_DELAY = 30  # Value in Seconds


# ------------------------------------------------------------------------------------------------------------------------

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



# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------

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
