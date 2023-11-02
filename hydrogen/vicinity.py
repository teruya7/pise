# coding: utf-8
#  Copyright (c) 2020 Kumagai group.
from dataclasses import dataclass

import numpy as np
from pymatgen.core import Lattice
from pymatgen.util.coord import pbc_shortest_vectors

PRECISION = 0.01


@dataclass(frozen=True)
class Vicinity:

    origin: tuple
    radius: float
    lattice: Lattice
    label: str = None

    def __post_init__(self):
        object.__setattr__(self, 'origin', tuple(self.origin))
        _d = np.linalg.norm(pbc_shortest_vectors(self.lattice,
                                                 self.origin, (0, 0, 0)))
        object.__setattr__(self, '_sort_key', _d)

    def within(self, another_coords):
        # d = frac_dist_to_real_dist(self.origin, another_coords, self.basis_vector)
        d = np.linalg.norm(pbc_shortest_vectors(self.lattice,
                                                self.origin, another_coords))
        return d <= self.radius - PRECISION

    @property
    def key(self):
        return self._sort_key

    def __eq__(self, other: "Vicinity"):
        return self.within(other.origin)


class Vicinities(set):

    def __init__(self, lattice=None, *args, **kwargs):
        self._lattice = lattice if lattice else None
        super().__init__(*args, **kwargs)

    @property
    def lattice(self):
        return self._lattice

    def add(self, other):
        if not isinstance(other, Vicinity):
            raise TypeError("Element must be vicinity.")
        if self._lattice != other.lattice:
            raise TypeError("basis_vector must be unique")
        if other in self:
            raise ValueError("The point is in other vicinity.")
        super().add(other)

    def grouping(self):
        groups = []
        for v in self:
            for group in groups:
                if v in group:
                    group.unsafe_add(v)
                    break
            else:
                new_vics = Vicinities(lattice=self.lattice)
                new_vics.unsafe_add(v)
                groups.append(new_vics)

        return groups

    def unsafe_add(self, value):
        super().add(value)  # check only hash

    def __contains__(self, other_v: Vicinity):
        if len(self) == 0:
            return False
        sort_self = sorted(self, key=lambda x: abs(x.key - other_v.key))
        for vi in sort_self:
            if abs(vi.key - other_v.key) > vi.radius + PRECISION:
                return False
            if other_v == vi:
                return True
        return False

    def __and__(self, other):
        result = Vicinities(lattice=self.lattice)
        for o in other:
            for s in self:
                if o == s:
                    result.unsafe_add(s)
                    result.unsafe_add(o)
        return result

    def __or__(self, other):
        result = Vicinities(lattice=self.lattice)
        for s in self:
            result.unsafe_add(s)
        for o in other:
            result.unsafe_add(o)
        return result

    def __le__(self, other):
        for s in self:
            if s not in other:
                return False
        return True

    def __lt__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        for o in other:
            if o not in self:
                return False
        return True

    def __gt__(self, other):
        raise NotImplementedError

    def __xor__(self, other):
        raise NotImplementedError

    def __sub__(self, other):
        raise NotImplementedError

    def isdisjoint(self, s):
        raise NotImplementedError

    def issubset(self, s):
        raise NotImplementedError

    def issuperset(self, s):
        raise NotImplementedError


def frac_dist_to_real_dist(fc1, fc2, basis_vector):
    fc1, fc2 = np.array(fc1), np.array(fc2)
    bv = np.array(basis_vector)
    return np.linalg.norm((fc2 - fc1) * bv)
