from collections import defaultdict
from pymatgen.io.vasp import Poscar
from pymatgen.io.vasp import Kpoints
import yaml
from yaml.representer import Representer

def make_extra_info_json():
    extra_info = defaultdict(dict)

    poscar = Poscar.from_file("POSCAR")
    poscar_dict = poscar.as_dict()
    extra_info["POSCAR"]["a"] = poscar_dict["structure"]["lattice"]["a"]
    extra_info["POSCAR"]["b"] = poscar_dict["structure"]["lattice"]["b"]
    extra_info["POSCAR"]["c"] = poscar_dict["structure"]["lattice"]["c"]
    extra_info["POSCAR"]["number_of atoms"] = sum(poscar.natoms)

    kpoints = Kpoints.from_file("KPOINTS")
    kpoints_dict = kpoints.as_dict()
    extra_info["KPOINTS"]["kpoints"] = kpoints_dict["kpoints"]
    extra_info["KPOINTS"]["shift"] = kpoints_dict["usershift"]

    with open("extra_info.yaml", "w") as f:
        yaml.add_representer(defaultdict, Representer.represent_dict)
        yaml.dump(extra_info, f, default_flow_style=False)
