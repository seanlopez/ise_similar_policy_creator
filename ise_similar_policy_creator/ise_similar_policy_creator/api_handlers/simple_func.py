from jinja2 import Template

def ise_info_render(template_file, output_file, data_dict):
    template_file = open(template_file, "r", encoding="utf-8")
    template = Template(template_file.read())

    info_content = template.render(
        address=data_dict["address"],
        username=data_dict["username"],
        password=data_dict["password"]
    )

    template_file.close()

    output = open(output_file, "w", encoding="utf-8")
    output.write(info_content)
    output.close()
