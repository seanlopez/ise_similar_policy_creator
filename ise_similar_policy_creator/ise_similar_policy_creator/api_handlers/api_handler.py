import json
from jinja2 import Template
import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class api_handler(object):
    def __init__(self, ise_configure_json_path, input_data_file=None):
        # read the data file which generated in uploading phase
        self.input_data = None
        self.group_data_dict = None
        self.input_data_row = 0
        if input_data_file != None:
            data_file = open(input_data_file, "r")
            data = json.loads(data_file.read())
            self.input_data = data
            self.input_data_row = len(data)

        # read the configuration file
        configuration_file = open(ise_configure_json_path, "r", encoding="utf-8")
        configuration = json.loads(configuration_file.read())
        self.ise_url = configuration["address"]
        self.ise_username = configuration["username"]
        self.ise_password = configuration["password"]

    def get_api_lanucher(self, api_uri):
        uri = self.ise_url + api_uri
        req = requests.get(uri, headers={'accept': 'application/json', 'Content-Type': 'application/json'}, auth=(self.ise_username, self.ise_password), verify=False)
        return req.text

    def post_api_lanucher(self, api_uri, payload_content):
        uri = self.ise_url + api_uri
        req = requests.post(uri, headers={'accept': 'application/json', 'Content-Type': 'application/json'}, auth=(self.ise_username, self.ise_password), verify=False, data=payload_content)
        return req.status_code

    def authorization_profile_api_payload_generator(self, template_path):
        '''
        Iterator, generate the authorization profile creation required API payload
        '''
        # Counter & output api payload string
        i = 0
        api_payload = ""

        # open the authorization profile template
        template_file = open(template_path, "r", encoding="utf-8")
        template = Template(template_file.read())

        while i < len(self.input_data):
            current_data_line = self.input_data[i]
            vlan_id = int(current_data_line[2].replace("\n", ""))
            api_payload = template.render(
                vlan_id=vlan_id
            )
            yield api_payload
            i = i + 1

    def authorization_policy_api_payload_generator(self, template_path):
        '''
        Iterator, create the authorization policy
        '''
        # Counter & output api payload string
        i = 0
        api_payload = ""

        # open the authorization profile template
        template_file = open(template_path, "r", encoding="utf-8")
        template = Template(template_file.read())

        while i < len(self.input_data):
            current_data_line = self.input_data[i]
            vlan_id = int(current_data_line[2].replace("\n", ""))
            join_point = current_data_line[0]
            group_full_name = current_data_line[1]
            group_name = group_full_name.split("/")[-1]
            api_payload = template.render(
                vlan_id=vlan_id,
                join_point=join_point,
                group_full_name=group_full_name,
                group_name=group_name
            )
            yield api_payload
            i = i + 1

    def group_checking_auto(self):
        for ad_join_point in self.group_data_dict.keys():
            result = self.group_checking(self.group_data_dict[ad_join_point], ad_join_point)
            # if all group can be find in specific AD join point, the func group_checking will return None
            # for example, all group in tianqi.com can be find, then group_checking func will return None
            # in this case, should continue the loop, then the checking for next AD joint point will be start
            if result == None:
                continue
            else:
                return self.group_checking(self.group_data_dict[ad_join_point], ad_join_point)
        return True

    def group_checking(self, group_list, join_point_name):
        '''
        check whether the target group is existing
        '''
        # retrieve all ad group info from specific group and add into list
        try:
            ad_grp_response = json.loads(self.get_api_lanucher(":9060/ers/config/activedirectory/name/"+join_point_name))
            ad_group_list = []
        except Exception as e:
            return " Cannot find the AD Joint Point - " + join_point_name + " in target ISE"

        #print(ad_grp_response["ERSActiveDirectory"])
        for grp in ad_grp_response["ERSActiveDirectory"]["adgroups"]["groups"]:
            ad_group_list.append(grp["name"])

        # print(ad_group_list)

        # check whether any group was not added into ISE yet
        for group_in_sheet in group_list:
            if group_in_sheet not in ad_group_list:
                return "The group - " + group_in_sheet + " cannot be find in AD Joint Point - " + join_point_name
        #    return True


    def authorization_profile_checking(self):
        '''
        check whether the created authorizsation profile is existing
        '''
        pass

    def ad_group_dict_creator(self):
        '''
        create the dict like (base on the self.input_data):
        {
            "ad_join_point_name_1": [group1, group2],
            "ad_join_point_name_2": [group1, group2],
            ...
        }
        the dict can be used for group checking
        '''
        ad_join_point_group_dict = {}
        for line_list in self.input_data:
            if line_list[0] in ad_join_point_group_dict.keys():
                ad_join_point_group_dict[line_list[0]].append(line_list[1])
            else:
                ad_join_point_group_dict[line_list[0]] = [line_list[1]]
        self.group_data_dict = ad_join_point_group_dict

    def get_all_policy_set(self):
        '''
        Get All Policy Set from the ISE
        '''
        policy_set_api_response = self.get_api_lanucher("/api/v1/policy/network-access/policy-set")
        policy_set_api_response_json = json.loads(policy_set_api_response)
        policy_set_api_response_list = policy_set_api_response_json["response"]

        api_response_data_list = []

        # get policy-set name and id in the dict
        for dict in policy_set_api_response_list:
            data_dict = {}
            data_dict["name"] = dict["name"]
            data_dict["id"] = dict["id"]
            api_response_data_list.append(data_dict)

        return api_response_data_list


if __name__ == "__main__":
    api_handler = api_handler("ise_configuration.json", "input_file_data.json")

    print(api_handler.input_data)

    policy_generator = api_handler.authorization_policy_api_payload_generator(
        "./jinja2_templates/authorization_policy_payload_template.j2")
    print(policy_generator.__next__())

    # api_handler.ad_group_dict_creator()
    # print(api_handler.group_data_dict)

    # print(api_handler.group_checking_auto())
    # print(api_handler.input_data_row)
    # print(api_handler.group_checking(["cisco1"], "secteam.com"))

    '''
    result = api_handler.group_checking(["tianqi.com/Users/cisco1", "tianqi.com/Users/cisco2"], "tianqi.com")
    print(result)

    policy_set_result = api_handler.get_all_policy_set()
    print(policy_set_result)
    '''

    '''

    get_result = api_handler.get_api_lanucher(":9060/ers/config/activedirectory/name/tianqi.com")
    print(json.loads(get_result))


    
    profile_generator = api_handler.authorization_profile_api_payload_generator("./jinja2_templates/authorization_profile_payload_template.j2")
    policy_generator = api_handler.authorization_policy_api_payload_generator(
        "./jinja2_templates/authorization_policy_payload_template.j2")

    result = api_handler.get_api_lanucher("/api/v1/policy/network-access/policy-set")

    print(json.loads(result))

    
    print(profile_generator.__next__())
    print(policy_generator.__next__())

    print(profile_generator.__next__())
    print(policy_generator.__next__())
    '''
