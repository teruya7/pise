from collections import defaultdict
from pymatgen.io.vasp import Poscar
from pymatgen.io.vasp import Kpoints
import yaml
from yaml.representer import Representer

def make_supercell_info_yaml():
    supercell_info = defaultdict(dict)

    poscar = Poscar.from_file("POSCAR")
    poscar_dict = poscar.as_dict()
    supercell_info["POSCAR"]["a"] = poscar_dict["structure"]["lattice"]["a"]
    supercell_info["POSCAR"]["b"] = poscar_dict["structure"]["lattice"]["b"]
    supercell_info["POSCAR"]["c"] = poscar_dict["structure"]["lattice"]["c"]
    supercell_info["POSCAR"]["number_of atoms"] = sum(poscar.natoms)

    kpoints = Kpoints.from_file("KPOINTS")
    kpoints_dict = kpoints.as_dict()
    supercell_info["KPOINTS"]["kpoints"] = kpoints_dict["kpoints"]
    supercell_info["KPOINTS"]["shift"] = kpoints_dict["usershift"]

    with open("supercell_info.yaml", "w") as f:
        yaml.add_representer(defaultdict, Representer.represent_dict)
        yaml.dump(supercell_info, f, default_flow_style=False)
