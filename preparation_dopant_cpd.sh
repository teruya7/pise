#!/bin/bash

dopant="$1"
element1="$2"
element2="$3"
element3="$4"

#利用しているスパコンを指定
system=ito

function prepare_job_script(){
    resource=1
    job_script_name=run6.4.1_"$resource".sh
    cp "$HOME"/pise/"$system"/"$job_script_name" ./
    touch ready_for_submission.txt
}

mkdir -p "$dopant"/cpd
cd "$dopant"/cpd
if [ $# -eq 3 ]; then
    pydefect_vasp mp -e $dopant $element1 $element2 --e_above_hull 0.0005 
else
    pydefect_vasp mp -e $dopant $element1 $element2 $element3 --e_above_hull 0.0005 
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
