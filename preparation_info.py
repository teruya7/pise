def repreparation(target_dir,repreparation_list,preparation_info_dict):
    if repreparation_list is not None:
            if target_dir in repreparation_list:
                preparation_info_dict[target_dir] = False