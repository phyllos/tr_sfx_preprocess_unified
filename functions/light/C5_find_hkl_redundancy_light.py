import os
import glob
import argparse
import h5py
import numpy as np


def find_hkl_redundancy_light(hklI_folder, hkl_max_file, data_name, folder_path='.'):
    hmax, kmax, lmax = np.loadtxt(hkl_max_file, dtype=int).reshape(-1)[:3]
    redundancy = np.zeros((hmax + 1, kmax + 1, lmax + 1), dtype=np.int32)
    for fn in glob.glob(os.path.join(hklI_folder, '*_hklI.dat')):
        arr = np.loadtxt(fn, ndmin=2)
        if arr.size == 0:
            continue
        for h, k, l in arr[:, :3].astype(int):
            if 0 <= h <= hmax and 0 <= k <= kmax and 0 <= l <= lmax:
                redundancy[h, k, l] += 1
    out = os.path.join(folder_path, f'redundancy_{data_name}.hdf5')
    with h5py.File(out, 'w') as h5:
        h5.create_dataset('redundancy', data=redundancy)
        h5.create_dataset('h_max', data=hmax)
        h5.create_dataset('k_max', data=kmax)
        h5.create_dataset('l_max', data=lmax)
    print(f'Saved {out}')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hklI_folder')
    p.add_argument('hkl_max_file')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    args = p.parse_args()
    find_hkl_redundancy_light(args.hklI_folder, args.hkl_max_file, args.data_name, args.folder)
