#!/bin/bash

dopant="$1"
substitution_target="$2"

#利用しているスパコンを指定
system=ito

function prepare_job_script(){
    resource=4
    job_script_name=run6.4.1_"$resource".sh
    cp "$HOME"/support_library/"$system"/"$job_script_name" ./
    touch ready_for_submission.txt
}

mkdir -p "$dopant"/defect
cd "$dopant"/defect

cp ../../defect/supercell_info.json ./
pydefect ds -d $dopant -k "$dopant"_i "$dopant"_"$substitution_target"
pydefect_vasp de 
for i in */
do 
    cd $i
    if [ ! -e vasprun.xml ]; then
        vise vs -t defect -uis SYMPREC 1e-4 --options only_even_num_kpts True 
        prepare_job_script 
    fi 
    cd ../
done 