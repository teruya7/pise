#!/bin/bash

pydefect_vasp u -vb band_nsc/vasprun.xml -ob band_nsc/OUTCAR-finish -odc dielectric/OUTCAR-finish -odi dielectric/OUTCAR-finish 

cd band
vise pb
cd ../band_nsc
vise pb
cd ../dos
vise pd
vise em -c 16 -t 300
cd ../abs
vise pdf -ckk