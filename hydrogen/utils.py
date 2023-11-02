# coding: utf-8
#  Copyright (c) 2020 Kumagai group.

import numpy as np

from pymatgen.core import Structure
from pymatgen.symmetry.groups import SpaceGroup
from vise.util.structure_symmetrizer import StructureSymmetrizer


def _get_orbit(structure, symmetry_ops, p, radius):
    """
    NOTE: THIS method is MODIFIED from pymatgen.symmetry.groups.SpaceGroup

    Returns the orbit for a point.

    Args:
        p: Point as a 3x1 array.
        tol: Tolerance for determining if sites are the same. 1e-5 should
            be sufficient for most purposes. Set to 0 for exact matching
            (and also needed for symbolic orbits).

    Returns:
        ([array]) Orbit for point.
    """
    orbit = []
    for o in symmetry_ops:
        pp = o.operate(p)
        pp = np.mod(np.round(pp, decimals=10), 1)
        # if not in_array_list(orbit, pp, tol=tol):
        if is_in_sphere(structure, orbit, pp, radius):
            continue
        orbit.append(pp)
    return orbit


def do_symmetry_operations(conventional_structure: Structure,
                           frac_coords,
                           radius: float = 0.01):
    symmetrizer = StructureSymmetrizer(conventional_structure)
    sg = SpaceGroup.from_int_number(symmetrizer.sg_number)
    orbit_fcs = np.array(_get_orbit(symmetry_ops=sg.symmetry_ops,
                                    structure=conventional_structure,
                                    p=frac_coords, radius=radius))
    orbit_fcs = force_positive_coords(orbit_fcs)

    return np.round(orbit_fcs, decimals=5)


def force_positive_coords(orbit_fcs):
    orbit_fcs += 1.0  # add 1 to be set as positive value
    orbit_fcs -= np.floor(orbit_fcs)
    return orbit_fcs


def is_in_sphere(structure, occupied_fcs, test_fc, radius):
    if len(occupied_fcs) == 0:
        return False
    dist_from_pos = structure.lattice.get_all_distances(
        fcoords1=occupied_fcs, fcoords2=test_fc)
    return np.any(dist_from_pos < radius)

