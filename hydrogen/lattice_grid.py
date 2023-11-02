# coding: utf-8
#  Copyright (c) 2020 Kumagai group.
from math import ceil

import numpy as np
from pymatgen.core import Structure


class LatticeGrid:

    def __init__(self,
                 structure: Structure,
                 mesh: float = 1.0):
        """

        :param structure: input structure
        :param mesh: mesh for generate grids (in Å)
        """
        self.structure = structure.copy()
        self._mesh = mesh
        self.num_grids = self._set_num_grids()
        print(f"initial grid points: {self.num_grids}")
        self.grid_points = self.create_grid_points()
        print(f"actual mesh distances: {self.actual_mesh}")

    def _set_num_grids(self):
        a, b, c = self.structure.lattice.abc
        return tuple(ceil(lc / self._mesh) for lc in (a, b, c))

    @property
    def mesh(self):
        return self._mesh

    @property
    def actual_mesh(self):
        a, b, c = self.structure.lattice.abc
        return a/self.num_grids[0], b/self.num_grids[1], c/self.num_grids[2]

    def create_grid_points(self):
        a_fcs = np.linspace(0, 1, self.num_grids[0], endpoint=False)
        b_fcs = np.linspace(0, 1, self.num_grids[1], endpoint=False)
        c_fcs = np.linspace(0, 1, self.num_grids[2], endpoint=False)
        all_fcs = []
        for ac in a_fcs:
            for bc in b_fcs:
                for cc in c_fcs:
                    all_fcs.append([ac, bc, cc])
        return all_fcs

    def remove_collisions(self, min_dist=0.8):
        """
        COPIED and MODIFIED FROM
        pymatgen.analysis.defects.utils.ChargeDensityAnalyzer.remove_collisions

        Remove predicted sites that are too close to existing atoms in the
        structure.

        Args:
            min_dist (float): The minimum distance (in Angstrom) that
                a predicted site needs to be from existing atoms. A min_dist
                with value <= 0 returns all sites without distance checking.
        """
        s_f_coords = self.structure.frac_coords
        f_coords = np.array(self.grid_points)

        dist_matrix = self.structure.lattice.get_all_distances(f_coords,
                                                               s_f_coords)
        all_dist = np.min(dist_matrix, axis=1)
        new_f_coords = []

        for i, f in enumerate(f_coords):
            if all_dist[i] > min_dist:
                new_f_coords.append(f)
        self.grid_points = new_f_coords
        print(f"Remove grid points close to atoms.")

    def get_structure_with_interstitial(self, element="H"):
        result = self.structure.copy()
        for fc in self.grid_points:
            result.append(element, fc)

        return result

