#!/bin/bash

name="$1"
mpcode="$2"
functional="${3:-pbesol}"

#利用しているスパコンを指定
system=ito

function prepare_job_script(){
    resource=1
    job_script_name=run6.4.1_"$resource".sh
    cp "$HOME"/pise/"$system"/"$job_script_name" ./
    touch ready_for_submission.txt
}

mkdir -p "$name"_"$mpcode"/"$functional"/unitcell/opt
cd "$name"_"$mpcode"/"$functional"
cp /"$HOME"/support_library/vise_"$functional".yaml vise.yaml
cd unitcell/opt

if [ $functional = pbesol ]; then
    vise gp -m $mpcode
fi

if [ $functional != pbesol ]; then
    cp ../../../pbesol/unitcell/opt/POSCAR ./
fi

vise vs -uis ENCUT 520
prepare_job_script 

