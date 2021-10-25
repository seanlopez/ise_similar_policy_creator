import requests
import urllib3
import json


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class api_applier(object):
    def __init__(self, config_json):
        config_file = open(config_json, "r")
        config = json.loads(config_file.read())
        self.address = config["address"]
        self.api = config["api"]
        self.username = config["username"]
        self.password = config["password"]

    def get_info(self):
        uri = self.address + self.api
        req = requests.get(uri, headers={'accept': 'application/json', 'Content-Type': 'application/json'},auth=(self.username, self.password), verify=False)
        return req.text

    def perform_configure(self, payload_content):
        uri = self.address + self.api
        req = requests.post(uri, headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                           auth=(self.username, self.password), verify=False, data=payload_content)
        return req.status_code

if __name__ == "__main__":
    api_applier = api_applier("ise_configure.json")
    payload_json = open("api_payload.json", "r")
    payload_content = payload_json.read()
    print(api_applier.perform_configure(payload_content))
