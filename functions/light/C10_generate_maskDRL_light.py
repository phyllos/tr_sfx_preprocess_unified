import os
import argparse
import h5py
import numpy as np
from scipy import sparse
from sparse_file_management import write_sparse


def generate_maskDRL_light(input_file, output_file=None, a=54.95, b=116.5, c=117.7):
    """C10 optional: mask reflections whose q is beyond per-snapshot DRL."""
    if output_file is None:
        folder = os.path.dirname(os.path.abspath(input_file))
        stem = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(folder, f'maskDRL_{stem}.hdf5')
    with h5py.File(input_file, 'r') as fin:
        h = np.asarray(fin['miller_h'][()]).squeeze()
        k = np.asarray(fin['miller_k'][()]).squeeze()
        l = np.asarray(fin['miller_l'][()]).squeeze()
        DRL = np.asarray(fin['DRL'][()]).squeeze()
        q = np.sqrt((h / a) ** 2 + (k / b) ** 2 + (l / c) ** 2)
        rows, cols = [], []
        for i, drl in enumerate(DRL):
            good = np.flatnonzero(q <= drl)  # SACLA DRL is q, not d.
            rows.extend([i] * len(good))
            cols.extend(good.tolist())
        mask = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(DRL), len(q))).tocsc()
    with h5py.File(output_file, 'w') as fout:
        write_sparse(fout, 'maskDRL', mask)
    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    args = p.parse_args()
    generate_maskDRL_light(args.input_file, args.output)
