from __future__ import annotations

import numpy as np
from pyxtal.symmetry import get_wyckoffs


def get_hkl_asymm_table(
    spacegroup_num: int,
    h_max: int = 10,
    k_max: int = 10,
    l_max: int = 10,
    positiveOctant: bool = True,
):
    """Create the legacy lookup table mapping HKL values to an asymmetric unit."""
    symmetry_operation = get_wyckoffs(spacegroup_num)
    operations = [
        op.affine_matrix[:3, :3].T.astype(int)
        for op in symmetry_operation[0]
    ]
    table = np.empty((2*h_max+1, 2*k_max+1, 2*l_max+1, 3), dtype=int)
    done = np.zeros((2*h_max+1, 2*k_max+1, 2*l_max+1), dtype=bool)

    for h in range(-h_max, h_max + 1):
        for k in range(-k_max, k_max + 1):
            for l in range(-l_max, l_max + 1):
                if done[h, k, l]:
                    continue
                hkl = np.asarray([[h, k, l]]).T
                candidates = np.empty((3, len(operations) * 2), dtype=int)
                for index, operation in enumerate(operations):
                    transformed = (operation @ hkl).flatten()
                    candidates[:, index * 2] = transformed
                    candidates[:, index * 2 + 1] = -transformed

                if positiveOctant:
                    preferred_indices = np.where(np.all(candidates >= 0, axis=0))[0]
                    if preferred_indices.size == 0:
                        preferred = candidates[:, 0]
                    else:
                        preferred_candidates = np.unique(candidates[:, preferred_indices], axis=1)
                        preferred = preferred_candidates[:, np.argmax(preferred_candidates[0] - preferred_candidates[1])]
                else:
                    preferred = candidates[:, 0]

                for candidate in candidates.T:
                    H, K, L = map(int, candidate)
                    table[H, K, L, :] = preferred
                    done[H, K, L] = True
    return table
