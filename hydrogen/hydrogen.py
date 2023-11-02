# coding: utf-8
#  Copyright (c) 2020 Kumagai group.
from collections import defaultdict
from pymatgen.io.vasp import Chgcar
import numpy as np
from pymatgen.core import Structure
from hydrogen.charge_density_analyzer import ChargeDensityAnalyzer
from vise.util.centering import Centering
from vise.util.structure_symmetrizer import StructureSymmetrizer

from hydrogen.lattice_grid import LatticeGrid
from hydrogen.utils import do_symmetry_operations, \
    force_positive_coords
from hydrogen.vicinity import Vicinities, Vicinity


def make_poscar_w_uniform_gridpoints(args):
    lg = LatticeGrid(structure=args.base_structure,
                     mesh=args.mesh)
    lg.remove_collisions()
    result = lg.get_structure_with_interstitial()
    result.to(filename="POSCAR_with_gridpoints", fmt="POSCAR")


def make_poscar_w_unique_gridpoints(args):
    symmetrizer = StructureSymmetrizer(args.base_structure)
    cs = symmetrizer.conventional
    lg = LatticeGrid(structure=cs, mesh=args.mesh)
    print("Symmetry operation is performed with conventional settings...")
    lg.remove_collisions(min_dist=args.min_dist)
    c_groups, src_fc = _get_unique_gridpoints(structure=cs,
                                              gridpoints=lg.grid_points,
                                              radius=args.mesh / 2)
    centering = Centering.from_string(symmetrizer.centering)
    p_to_c = np.array(np.linalg.inv(np.array(centering.conv_to_primitive)))
    p_groups = convert_p_group(c_groups, p_to_c)
    _write_sequential_poscars(cs, c_groups, prefix="B")
    _write_sequential_poscars(args.base_structure, p_groups, prefix="P")

    c_result = cs.copy()
    for cfc in src_fc.values():
        c_result.append("H", cfc)
    c_result.to(filename="BPOSCAR_with_gridpoints", fmt="POSCAR")
    p_result = args.base_structure.copy()
    for pfc in p_groups.values():
        p_result.append("H", pfc[0])
    p_result.to(filename="PPOSCAR_with_gridpoints", fmt="POSCAR")


def _grouping_coords(data, structure, radius):
    result = dict()
    groups_label = defaultdict(list)
    groups_energy = defaultdict(list)
    group_num = 0
    vicinities_dict = dict()
    for name, hfc, energy in data:
        h_v = Vicinity(hfc, radius, structure.lattice)
        grouped_area = Vicinities(lattice=structure.lattice)
        hfc_orbit = do_symmetry_operations(conventional_structure=structure,
                                           frac_coords=hfc,
                                           radius=0.025)
        hfc_orbit = set(tuple(o.tolist()) for o in hfc_orbit)

        for fc in hfc_orbit:
            grouped_area.unsafe_add(Vicinity(fc, radius, structure.lattice))

        for group, vs in vicinities_dict.items():
            if h_v in vs:
                groups_label[group].append(name)
                groups_energy[group_num].append(energy)
                break
        else:
            group_num += 1
            result[f"g{group_num}"] = hfc_orbit
            vicinities_dict[group_num] = grouped_area
            groups_label[group_num].append(name)
            groups_energy[group_num].append(energy)

    for group in groups_label:
        print(f"-[g{group}]---------------------------------------------------")
        print(groups_energy[group][0], groups_energy[group][-1])
        print(groups_label[group])
        print("-------------------------------------------------------")
    return result


def _get_unique_gridpoints(structure: Structure, gridpoints: list,
                           radius: float):
    structure = structure.copy()
    lattice = structure.lattice
    label_to_points = dict()
    label_to_src_gridpoint = dict()

    reserved_area = Vicinities(lattice=lattice)
    label_number = 1  # key
    for p in gridpoints:
        p_v = Vicinity(p, radius, lattice)
        if p_v in reserved_area:
            continue

        p_orbit = do_symmetry_operations(conventional_structure=structure,
                                         frac_coords=p)
        label_to_points[label_number] = set(tuple(fc) for fc in p_orbit)
        label_to_src_gridpoint[label_number] = p

        for fc in set(tuple(o.tolist()) for o in p_orbit):
            reserved_area.unsafe_add(Vicinity(fc, radius, lattice))
        label_number += 1

    return label_to_points, label_to_src_gridpoint


def _write_sequential_poscars(structure: Structure,
                              u_gridpoints, species="H", prefix="B"):
    for key, fcs in u_gridpoints.items():
        s = structure.copy()
        for xfc in fcs:
            s.append(species, xfc)
        s.merge_sites(tol=0.01, mode="delete")
        s.sort(key=lambda x: x.specie.number, reverse=True)
        s.to(filename=f"{prefix}POSCAR_{key}", fmt="POSCAR")

def get_local_extrema(path_to_charge_info, path_to_poscar, thresold, radius, find_min=False, near_o_sites=False):
    charge_info = Chgcar.from_file(path_to_charge_info)
    cda = ChargeDensityAnalyzer(charge_info)
    max_value = cda.chgcar.data["total"].max()
    cda.get_local_extrema(find_min=find_min,
                          threshold_abs=max_value*thresold)
    cda.remove_collisions(min_dist=0.5)
    print(cda.extrema_df)

    structure = Structure.from_file(path_to_poscar)
    ss = StructureSymmetrizer(structure)
    centering = Centering.from_string(ss.centering)
    c_to_p = np.array(centering.conv_to_primitive)
    p_to_c = np.array(np.linalg.inv(c_to_p))
    raw_data = []
    fcs = cda.extrema_coords
    chgs = cda.extrema_df["Charge Density"]
    cnt = 0
    for fc, chg in zip(fcs, chgs):
        if near_o_sites is True:
            if _near_o_sites(path_to_poscar, fc) is False:
                continue
        conventional_fc = np.dot(fc, c_to_p).tolist()
        raw_data.append((cnt, conventional_fc, chg))
        cnt += 1

    c_groups = _grouping_coords(raw_data, ss.conventional, radius)
    p_groups, site_coordinate_dict = convert_p_group(c_groups, p_to_c)
    _write_sequential_poscars(ss.conventional, c_groups, prefix="B")
    _write_sequential_poscars(structure, p_groups, prefix="P")

    return site_coordinate_dict

# def get_local_extrema(args):
#     cda = ChargeDensityAnalyzer(args.locpot)
#     max_value = cda.chgcar.data["total"].max()
#     cda.get_local_extrema(find_min=args.find_min,
#                           threshold_abs=max_value*args.thresold)
#     cda.remove_collisions(min_dist=0.5)
#     print(cda.extrema_df)

#     ss = StructureSymmetrizer(args.base_structure)
#     centering = Centering.from_string(ss.centering)
#     c_to_p = np.array(centering.conv_to_primitive)
#     p_to_c = np.array(np.linalg.inv(c_to_p))
#     raw_data = []
#     fcs = cda.extrema_coords
#     chgs = cda.extrema_df["Charge Density"]
#     cnt = 0
#     for fc, chg in zip(fcs, chgs):
#         if args.near_o_sites is True:
#             if _near_o_sites(args.base_structure, fc) is False:
#                 continue
#         conventional_fc = np.dot(fc, c_to_p).tolist()
#         raw_data.append((cnt, conventional_fc, chg))
#         cnt += 1

#     c_groups = _grouping_coords(raw_data, ss.conventional, args.radius)
#     p_groups, site_coordinate_dict = convert_p_group(c_groups, p_to_c)
#     _write_sequential_poscars(ss.conventional, c_groups, prefix="B")
#     _write_sequential_poscars(args.base_structure, p_groups, prefix="P")


def convert_p_group(c_groups, p_to_c):
    p_groups = {}
    site_coordinate_dict = {}
    for key, cfcs in c_groups.items():
        pfcs = [force_positive_coords(np.dot(cfc, p_to_c)).tolist()
                for cfc in cfcs]
        pfcs.sort(key=lambda x: np.linalg.norm(x))
        p_groups[key] = pfcs
        print(f"{key}: {pfcs[0][0]:.5f} {pfcs[0][1]:.5f} {pfcs[0][2]:.5f}")

        x = '{:.05f}'.format(pfcs[0][0])
        y = '{:.05f}'.format(pfcs[0][1])
        z = '{:.05f}'.format(pfcs[0][2])
        site_coordinate_dict[key] = [x, y, z]
    return p_groups, site_coordinate_dict


def _near_o_sites(s: Structure, fc):
    cc = np.dot(fc, s.lattice.matrix)
    nn = s.get_sites_in_sphere(pt=cc, r=1.2, include_image=True)
    nn_specie = [s.species_string for s in nn]
    return "O" in nn_specie



