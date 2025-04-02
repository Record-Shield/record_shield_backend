import requests
import time
from config import Config
import http.client
import json

management_token = None
token_expires_at = 0

def get_management_token():

    conn = http.client.HTTPSConnection("dev-4xalqwtpzkjsisfj.au.auth0.com")

    payload = "{\"client_id\":\"XdIWkZTnVSf5qdsxVMRLZWBVuhokGv8s\",\"client_secret\":\"aZZwlHzsnJFvDvoYJPCd43hLscLVpKHLv6TmiJ-e1Ip4epAipgiL5ok40CzCFCP5\",\"audience\":\"https://dev-4xalqwtpzkjsisfj.au.auth0.com/api/v2/\",\"grant_type\":\"client_credentials\",\"scope\":\"read:users\"}"

    headers = { 'content-type': "application/json" }

    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    data = res.read().decode("utf-8") 
    json_data = json.loads(data)      

    management_token = json_data.get("access_token")
    return management_token
