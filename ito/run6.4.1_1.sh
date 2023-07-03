#!/bin/bash
#PJM -L "rscunit=ito-a"
#PJM -L "rscgrp=ito-a-oc180153"
#PJM -L "vnode=1"
#PJM -L "vnode-core=36"
#PJM -L "elapse=120:00:00"
#PJM -j
#PJM -X

module load oneapi/2022.3.1

num_nodes=1
procs_per_node=36
num_procs=$((${procs_per_node}*${num_nodes}))
export I_MPI_HYDRA_BOOTSTRAP_EXEC=pjrsh
export I_MPI_HYDRA_HOST_FILE=$PJM_O_NODEINF
export I_MPI_DEVICE=rdma

#mpi=/usr/local/intel2017_up4/compilers_and_libraries_2017.4.196/linux/mpi/intel64/bin/mpirun
rep=/home/usr1/r70391a/scripts/repeatGeomOpt5.sh

kpt=`head -n 4 KPOINTS| tail -n 1`
if [ "$kpt" = "1 1 1" ]
then
  vasp=/home/usr1/r70391a/vasp6.4.1/vasp.6.4.1/bin/vasp_std
else
  vasp=/home/usr1/r70391a/vasp6.4.1/vasp.6.4.1/bin/vasp_std
fi
"""
if [ ! -e WAVECAR ]
then
  mkdir gga
  grep -v LHF INCAR| grep -v LCALCEPS| grep -v LORBIT| grep -v NSW | grep -v ALGO > gga/INCAR
  cp POSCAR POTCAR KPOINTS gga/
  cd gga
  $rep $mpi -n $num_procs -ppn $procs_per_node $vasp
  cp POSCAR-finish ../POSCAR
  cp WAVECAR ../
  cd ../
fi
"""
$rep mpirun -n $num_procs -ppn $procs_per_node $vasp
