#!/bin/bash

AEXX="$1"

#利用しているスパコンを指定
system=ito

function prepare_job_script(){
    resource=4
    job_script_name=run6.4.1_"$resource".sh
    cp "$HOME"/support_library/"$system"/"$job_script_name" ./
    touch ready_for_submission.txt
}

cd unitcell
mkdir band_nsc
cd band_nsc
if [ ! -e vasprun.xml ]; then
    cp "$HOME"/support_library/vise_nsc.yaml vise.yaml
    vise vs -t band -pd ../opt -x pbe0 -uis ALGO Subrot NELM 1 HFRCUT -1 AEXX $AEXX
    cp ../band/WAVECAR ./ 
    prepare_job_script 
fi 
