import os
import subprocess

#全ての計算が終了しているか確認
def check_calc_done(list):
    for i in list:
        if i:
            flag = True
        else:
            flag = False
            break
    return flag

#全ての計算が終了していれば解析を実行
def analysis(path, name, list, json_file, check_file, target_name=None):
    os.chdir(path)
    home = os.environ['HOME']
    if check_calc_done(list):
        print(f"calculation of {name} has been completed.")
        if name == "cpd":
            subprocess.run([f"sh {home}/support_library/analysis_{name}.sh {target_name}"], shell=True)
        else:
            subprocess.run([f"sh {home}/support_library/analysis_{name}.sh"], shell=True)
        if os.path.isfile(check_file):
            json_file[name] = True
            flag = True
        else:
            json_file[name] = False
            flag = False
    else:
        print(f"calculation of {name} has not been completed.")
        json_file[name] = False
        flag = False
    os.chdir("../")
    return flag

if __name__ == '__main__':
    print("これは自作モジュールです")