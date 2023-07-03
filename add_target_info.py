from pymatgen.ext.matproj import MPRester
import json
import argparse 
import os
from collections import defaultdict

MY_API_KEY = "em2ym4NUaNkGtFmKzqZ"
mp = MPRester(MY_API_KEY)

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mpcode')
args = parser.parse_args()

#target_info.jsonの読み込み
file_name = "target_info.json"
if os.path.isfile(file_name):
    flag = True
    print(f"Loading {file_name}")
    with open(file_name) as f:
        target_info = json.load(f)
else:
    flag = False
    print(f"Making {file_name}")
    target_info = defaultdict(dict)
    
# Properties you need:
basic_properties = ['pretty_formula', 'task_id', 'spacegroup.symbol', "elements"]

# Query criteria: must include O element; less than 3 types of elements; space group is not equal to 1; band gap value exists
criteria = {"task_id": args.mpcode}

# Retrieve material property data which satisfy query criteria
data = mp.query(criteria=criteria, properties=basic_properties)

if flag:
    target_info.append(data[0])
    with open(file_name, "w") as f:
        json.dump(target_info, f, indent=4)
else:
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)
