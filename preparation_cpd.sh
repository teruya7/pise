#!/bin/bash

element1="$1"
element2="$2"
element3="$3"

#利用しているスパコンを指定
system=ito

function prepare_job_script(){
    resource=1
    job_script_name=run6.4.1_"$resource".sh
    cp "$HOME"/pise/"$system"/"$job_script_name" ./
    touch ready_for_submission.txt
}

mkdir cpd
cd cpd
if [ $# -eq 2 ]; then
    pydefect_vasp mp -e $element1 $element2 --e_above_hull 0.0005 
else
    pydefect_vasp mp -e $element1 $element2 $element3 --e_above_hull 0.0005 
fi

for i in *_*/ 
do 
    cd $i 
    if [ ! -e vasprun.xml ]; then
        vise vs -uis ENCUT 520
        prepare_job_script 
    fi 
    cd ../ 
done
