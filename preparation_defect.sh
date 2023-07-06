#!/bin/bash

source "$HOME"/pise/conf.txt

function prepare_job_script(){
    cp "$HOME"/pise/"$system"/"$job_script_name_4" ./
    touch ready_for_submission.txt
}

mkdir defect
cd defect

pydefect s -p ../unitcell/dos/POSCAR-finish --max_atoms 150
pydefect_vasp le -v ../unitcell/dos/repeat-*/AECCAR{0,2} -i all_electron_charge 
pydefect_util ai --local_extrema volumetric_data_local_extrema.json -i 1 2 
pydefect ds 
pydefect_vasp de 
for i in */
do 
    cd $i
    if [ -e POSCAR-10 ]; then
        echo $i
        cp repeat-10/CONTCAR POSCAR
        rm -r OUTCAR-* progress-* POSCAR-*
    fi 

    if [ ! -e vasprun.xml ]; then
        vise vs -t defect -uis SYMPREC 1e-4 --options only_even_num_kpts True 
        prepare_job_script 
    fi 
    cd ../
done 