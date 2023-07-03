#!/bin/bash

name="$1"

ln -s ../unitcell/opt host
pydefect_vasp mce -d */ 
pydefect sre 
pydefect cv -t $name
pydefect pc 