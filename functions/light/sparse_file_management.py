from __future__ import annotations

import h5py
import numpy as np
from scipy import sparse


def read_vector(h5: h5py.File, name: str) -> np.ndarray:
    return np.asarray(h5[name][()]).squeeze()


def write_vector(h5: h5py.File, name: str, data) -> None:
    h5.create_dataset(name, data=np.asarray(data).squeeze())


def write_text(h5: h5py.File, name: str, text: str) -> None:
    h5.create_dataset(name, data=np.bytes_(text))


def read_sparse(h5: h5py.File, name: str) -> sparse.csc_matrix:
    """Read MATLAB v7.3 sparse groups or this package's native CSC groups."""
    group = h5[name]
    if "MATLAB_sparse" in group.attrs:
        n_rows = int(group.attrs["MATLAB_sparse"])
        jc = np.asarray(group["jc"][()], dtype=np.int64)
        ir = np.asarray(group["ir"][()], dtype=np.int64)
        data = np.asarray(group["data"][()], dtype=np.float64)
        return sparse.csc_matrix((data, ir, jc), shape=(n_rows, len(jc) - 1))

    data = np.asarray(group["data"][()], dtype=np.float64)
    indices = np.asarray(group["indices"][()], dtype=np.int64)
    indptr = np.asarray(group["indptr"][()], dtype=np.int64)
    shape = tuple(np.asarray(group["shape"][()], dtype=np.int64))
    return sparse.csc_matrix((data, indices, indptr), shape=shape)


def write_sparse(h5: h5py.File, name: str, matrix) -> None:
    matrix = matrix.tocsc()
    group = h5.create_group(name)
    group.attrs["format"] = "csc"
    group.create_dataset("data", data=matrix.data.astype(np.float64, copy=False))
    group.create_dataset("indices", data=matrix.indices.astype(np.int64, copy=False))
    group.create_dataset("indptr", data=matrix.indptr.astype(np.int64, copy=False))
    group.create_dataset("shape", data=np.asarray(matrix.shape, dtype=np.int64))


def copy_if_exists(fin: h5py.File, fout: h5py.File, names) -> None:
    for name in names:
        if name not in fin:
            continue
        obj = fin[name]
        if isinstance(obj, h5py.Dataset):
            fout.create_dataset(name, data=obj[()])
