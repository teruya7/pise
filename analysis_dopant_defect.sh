#!/bin/bash

ln -s ../../defect/perfect ./
echo 1 ; pydefect_vasp cr -d *_*/ perfect 
echo 2 ; pydefect efnv -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml 
echo 3 ; pydefect dsi -d *_*/ 
echo 4 ; pydefect_util dvf -d *_* 
echo 5 ; pydefect dsi -d *_*/ 
echo 6 ; pydefect_util dvf -d *_* 
echo 7 ; pydefect_vasp pbes -d perfect 
echo 8 ; pydefect_vasp beoi -d *_* -pbes perfect/perfect_band_edge_state.json 
echo 9 ; pydefect bes -d *_*/ -pbes perfect/perfect_band_edge_state.json 

cwd=$(pwd)
cd ../../defect
for i in *_*/
do 
    mkdir "$cwd"/"$i"
    cd $i
    cp band_edge_orbital_infos.json "$cwd"/"$i"
    cp band_edge_states.json "$cwd"/"$i"
    cp calc_results.json "$cwd"/"$i"
    cp correction.json "$cwd"/"$i"
    cp defect_entry.json "$cwd"/"$i"
    cp defect_structure_info.json "$cwd"/"$i"
    cd ../
done

cd $cwd
echo 10 ; pydefect dei -d *_*/ -pcr perfect/calc_results.json -u ../../unitcell/unitcell.yaml -s ../cpd/standard_energies.yaml 
echo 11 ; pydefect des -d *_*/ -u ../../unitcell/unitcell.yaml -pbes perfect/perfect_band_edge_state.json -t ../cpd/target_vertices.yaml 
echo 12 ; pydefect cs -d *_*/ -pcr perfect/calc_results.json 
echo 13 ; pydefect pe -d defect_energy_summary.json -l A ; pydefect pe -d defect_energy_summary.json -l B ; pydefect pe -d defect_energy_summary.json -l C ; pydefect pe -d defect_energy_summary.json -l D ; pydefect pe -d defect_energy_summary.json -l E ; pydefect pe -d defect_energy_summary.json -l F ; pydefect pe -d defect_energy_summary.json -l G ; pydefect pe -d defect_energy_summary.json -l H 