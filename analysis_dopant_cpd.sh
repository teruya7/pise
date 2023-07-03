#!/bin/bash

name="$1"

cwd=$(pwd)

ln -s ../../unitcell/opt host
cd ../../cpd
for i in *_*/
do
    mkdir "$cwd"/"$i"
    cd $i
    cp POSCAR-finish "$cwd"/"$i"
    cp OUTCAR-finish "$cwd"/"$i"
    cd ../
done

cd $cwd
pydefect_vasp mce -d */ 
pydefect sre 
pydefect cv -t $name
pydefect pc 