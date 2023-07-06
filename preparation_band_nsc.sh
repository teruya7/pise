#!/bin/bash

AEXX="$1"

source "$HOME"/pise/conf.txt

function prepare_job_script(){
    cp "$HOME"/pise/"$system"/"$job_script_name_4" ./
    touch ready_for_submission.txt
}

cd unitcell
mkdir band_nsc
cd band_nsc
if [ ! -e vasprun.xml ]; then
    cp "$HOME"/pise/vise_nsc.yaml vise.yaml
    vise vs -t band -pd ../opt -x pbe0 -uis ALGO Subrot NELM 1 HFRCUT -1 AEXX $AEXX
    cp ../band/WAVECAR ./ 
    prepare_job_script 
fi 
