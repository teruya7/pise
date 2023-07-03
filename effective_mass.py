import json
from collections import defaultdict
import yaml
from yaml.representer import Representer


def too_small_is_zero(num):
    if  num < 1e-6:
        num = 0
    else:
        num = format(num, '.2f')
    return num

def easy_to_see_effective_mass(type,input_json,output_json):
    tensor = input_json[type][0]
    tensor_list = []
    for vector in tensor:
        vector_list = []
        for scalar in vector:
            vector_list.append(too_small_is_zero(scalar))
        tensor_list.append(vector_list)
    output_json[type]= tensor_list
            
def revise_effective_mass_json():
    output_dict = defaultdict(dict)
    with open("effective_mass.json") as f:
        input_json = json.load(f)
    output_dict["concentrations"] = input_json["concentrations"]
    output_dict["temperature"] = input_json["temperature"]
    easy_to_see_effective_mass("p", input_json, output_dict)
    easy_to_see_effective_mass("n", input_json, output_dict)

    with open("effective_mass.yaml", "w") as f:
        yaml.add_representer(defaultdict, Representer.represent_dict)
        yaml.dump(output_dict, f, default_flow_style=False)
