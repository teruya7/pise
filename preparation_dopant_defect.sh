#!/bin/bash

dopant="$1"
substitution_target="$2"

source "$HOME"/pise/conf.txt

function prepare_job_script(){
    cp "$HOME"/pise/"$system"/"$job_script_name_4" ./
    touch ready_for_submission.txt
}

mkdir -p dopant_"$dopant"/defect
cd dopant_"$dopant"/defect

cp ../../defect/supercell_info.json ./
pydefect ds -d $dopant -k "$dopant"_i "$dopant"_"$substitution_target"
pydefect_vasp de 
for i in */
do 
    cd $i
    if [ -e POSCAR-10 ]; then
        cp repeat-10/CONTCAR POSCAR
        rm -r OUTCAR-* progress-* POSCAR-*
    fi 
    if [ ! -e vasprun.xml ]; then
        vise vs -t defect -uis SYMPREC 1e-4 --options only_even_num_kpts True 
        prepare_job_script 
    fi 
    cd ../
done 