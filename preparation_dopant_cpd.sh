#!/bin/bash

dopant="$1"
element1="$2"
element2="$3"
element3="$4"

source "$HOME"/pise/conf.txt

function prepare_job_script(){
    cp "$HOME"/pise/"$system"/"$job_script_name_1" ./
    touch ready_for_submission.txt
}

mkdir -p dopant_"$dopant"/cpd
cd dopant_"$dopant"/cpd
if [ $# -eq 3 ]; then
    pydefect_vasp mp -e $dopant $element1 $element2 --e_above_hull 0.0005 
else
    pydefect_vasp mp -e $dopant $element1 $element2 $element3 --e_above_hull 0.0005 
fi
for i in *_*/ 
do 
    cd $i 
    if [ -e POSCAR-10 ]; then
        cp repeat-10/CONTCAR POSCAR
        rm -r OUTCAR-* progress-* POSCAR-*
    fi 
    
    if [ ! -e vasprun.xml ]; then
        vise vs -uis ENCUT 520
        prepare_job_script
    fi 
    cd ../ 
done
