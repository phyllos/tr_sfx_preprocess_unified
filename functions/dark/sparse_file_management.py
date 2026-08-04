from __future__ import annotations

import numpy as np
from scipy import sparse


def write_sparse(matrix, name, h5):
    """Write a scipy sparse matrix using the legacy *_csr group convention."""
    matrix = matrix.tocsr()
    group = h5.create_group(f"{name}_csr")
    group.attrs["shape"] = matrix.shape
    group.create_dataset("data", data=matrix.data)
    group.create_dataset("indices", data=matrix.indices)
    group.create_dataset("indptr", data=matrix.indptr)


def load_sparse(name, h5):
    """Load legacy sparse groups, with a fallback for direct group names."""
    group_name = f"{name}_csr" if f"{name}_csr" in h5 else name
    group = h5[group_name]
    if "shape" in group.attrs:
        raw_shape = group.attrs["shape"]
    elif "shape" in group:
        raw_shape = group["shape"][()]
    else:
        raise KeyError(f"Sparse group {group_name!r} has no shape metadata")
    shape = tuple(int(v) for v in raw_shape)
    return sparse.csr_matrix(
        (
            np.asarray(group["data"][()]),
            np.asarray(group["indices"][()], dtype=np.int64),
            np.asarray(group["indptr"][()], dtype=np.int64),
        ),
        shape=shape,
    )
