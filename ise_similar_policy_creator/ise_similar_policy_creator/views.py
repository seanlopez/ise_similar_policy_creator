from django.shortcuts import render
from django.http import HttpResponse
from django.http import FileResponse
import os
from .api_handlers.api_handler import api_handler
from .api_handlers import simple_func
import json


def portal_display(request):
    return render(request, "index.html")

def deployment(request):
    # Get the policy set id
    form_dict = request.POST.dict()  # get all form info
    policy_set_id = form_dict["policysetselected"]

    # Create Object
    api_controller = api_handler("./ise_similar_policy_creator/api_handlers/ise_configuration.json", "./ise_similar_policy_creator/api_handlers/input_file_data.json")

    # Group Checking
    api_controller.ad_group_dict_creator()
    checking_result = api_controller.group_checking_auto()
    if checking_result != True:
        return render(request, "deployment_page.html", {"checking": checking_result})

    # Generator - Authorization Profile Payload
    authorization_payload_generator = api_controller.authorization_profile_api_payload_generator("./ise_similar_policy_creator/api_handlers/jinja2_templates/authorization_profile_payload_template.j2")

    # Generator - Authorization Policy Payload
    policy_payload_generator = api_controller.authorization_policy_api_payload_generator("./ise_similar_policy_creator/api_handlers/jinja2_templates/authorization_policy_payload_template.j2")

    # Deploy the authorization profile & policy
    try:
        for row in range(api_controller.input_data_row):
            profile_payload = authorization_payload_generator.__next__()
            policy_payload = policy_payload_generator.__next__()
            print(policy_payload)
            api_controller.post_api_lanucher(":9060/ers/config/authorizationprofile", profile_payload)
            api_controller.post_api_lanucher(f"/api/v1/policy/network-access/policy-set/{ policy_set_id }/authorization", policy_payload)
    except Exception as e:
        return render(request, "deployment_page.html", {"checking": "API Post Error"})

    return render(request, "deployment_page.html", {"result": "Deployment Success, Please double check policy & Profile on ISE"})


def policy_set_selection(request):
    ise_api_controller = api_handler("./ise_similar_policy_creator/api_handlers/ise_configuration.json")
    try:
        api_response_data_list = ise_api_controller.get_all_policy_set()

        print(api_response_data_list)

        return render(request, "policy_set_selection.html", {"data": api_response_data_list})
    except Exception as e:
        # print(e)
        return render(request, "policy_set_selection.html")

def upload_file(request):
    if request.method == "POST":    # 请求方法为POST时，进行处理

        form_dict = request.POST.dict()   # get all form info
        print(form_dict)

        ise_info_dict = {
            "address": "https://" + form_dict["ipaddress"],
            "username": form_dict["username"],
            "password": form_dict["password"]
        }

        simple_func.ise_info_render("./ise_similar_policy_creator/api_handlers/jinja2_templates/ise_info_jinja.j2", "./ise_similar_policy_creator/api_handlers/ise_configuration.json", ise_info_dict)

        myFile =request.FILES.get("myfile", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return render(request, "index.html", {"upload_result": "No File selected, please upload the CSV file"})
        input_file = open(os.path.join("./input_files", "user_uploaded.csv"),'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():      # 分块写入文件
            input_file.write(chunk)
        input_file.close()

        try:
            uploaded_file = open(os.path.join("./input_files", "user_uploaded.csv"), 'r')
            lines = uploaded_file.readlines()
            if "Name,VLAN ID" not in lines[0]:
                os.system("rm -f " + "./input_files/" + "user_uploaded.csv")
                return render(request, "index.html",{"upload_result": "The file format is not correct, please download the template and upload again"})
            else:
                csv_length = len(lines)
                all_lines = []
                for line_num in range(1, csv_length):
                    all_lines.append(lines[line_num].split(","))
                input_file_data = open("./ise_similar_policy_creator/api_handlers/input_file_data.json", "w", encoding="utf-8")
                input_file_data.write(json.dumps(all_lines))
                input_file_data.close()
                return render(request, "preview.html", {"data": all_lines, "csv_length": csv_length-1})
        except Exception as e:
            print(e)
            os.system("rm -f " + "./input_files/" + "user_uploaded.csv")
            return render(request, "index.html", {"upload_result": "The uploaded file is not correct, please upload again"})


def csv_download(request):
    file = open(f'/csv_template/vlan_group_mapping.csv', 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="vlan_group_mapping_template.csv"'
    return response
