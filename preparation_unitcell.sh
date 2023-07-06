#!/bin/bash

functional="${1:-pbesol}"

source "$HOME"/pise/conf.txt

function prepare_job_script(){
    cp "$HOME"/pise/"$system"/"$job_script_name_1" ./
    touch ready_for_submission.txt
}

cd unitcell

if [ $functional = pbesol ]; then
    mkdir {band,dos,dielectric,abs,dielectric_rpa}

    cd band
    if [ ! -e vasprun.xml ]; then
        vise vs -t band -pd ../opt
        prepare_job_script 
    fi 
    
    cd ../dos
    if [ ! -e vasprun.xml ]; then
        vise vs -t dos -pd ../opt -uis LVTOT True LAECHG True KPAR 1 
        prepare_job_script 
    fi 
    
    cd ../abs
    if [ ! -e vasprun.xml ]; then
        vise vs -t dielectric_function -pd ../opt
        prepare_job_script 
    fi 
    
    cd ../dielectric
    if [ ! -e vasprun.xml ]; then
        vise vs -t dielectric_finite_field -pd ../opt -uis IBRION 6
        prepare_job_script 
    fi 
    

    cd ../dielectric_rpa
    if [ ! -e vasprun.xml ]; then
        vise vs -t dielectric_dfpt -pd ../opt -uis LRPA True
        prepare_job_script 
    fi 

fi

if [ $functional != pbesol ]; then
    mkdir {band,dos,dielectric,abs}

    cd band
    if [ ! -e vasprun.xml ]; then
        vise vs -t band -pd ../opt
        prepare_job_script 
    fi 
    
    cd ../dos
    if [ ! -e vasprun.xml ]; then
        vise vs -t dos -pd ../opt -uis LVTOT True LAECHG True KPAR 1 
        prepare_job_script 
    fi 
    
    cd ../abs
    if [ ! -e vasprun.xml ]; then
        vise vs -t dielectric_function -pd ../opt
        prepare_job_script 
    fi 

    cd ../dielectric
    if [ ! -e vasprun.xml ]; then
        vise vs -t dielectric_finite_field -d ../opt -uis IBRION 6
        prepare_job_script 
    fi 
    
fi


