import argparse 
import os
import subprocess

#カレントディレクトリのフォルダのリストを作成
def make_dir_list():
    list = []
    for f in os.listdir():
        if os.path.isdir(f):
            list.append(f)
    return list

def delete_duplication(path_to_criteria, path_to_target):
    #元のパスの記録
    cwd = os.getcwd()

    os.chdir(path_to_criteria)
    criteria_list = make_dir_list()

    os.chdir(cwd)
    os.chdir(path_to_target)
    target_list = make_dir_list()

    for i in target_list:
        if i in criteria_list:
            subprocess.run([f"rm -r {i}"], shell=True)
            print(f"{i} is duplication.")
    
    os.chdir(cwd)






