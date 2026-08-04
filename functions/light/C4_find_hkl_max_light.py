import os
import glob
import argparse
import numpy as np


def find_hkl_max_light(hklI_folder, data_name, folder_path='.'):
    hmax = kmax = lmax = 0
    for fn in glob.glob(os.path.join(hklI_folder, '*_hklI.dat')):
        arr = np.loadtxt(fn, ndmin=2)
        if arr.size == 0:
            continue
        hmax = max(hmax, int(np.max(np.abs(arr[:, 0]))))
        kmax = max(kmax, int(np.max(np.abs(arr[:, 1]))))
        lmax = max(lmax, int(np.max(np.abs(arr[:, 2]))))
    out = os.path.join(folder_path, f'hkl_max_{data_name}.dat')
    np.savetxt(out, np.asarray([[hmax, kmax, lmax]], dtype=int), fmt='%d')
    print(f'Saved {out}: h_max={hmax}, k_max={kmax}, l_max={lmax}')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hklI_folder')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    args = p.parse_args()
    find_hkl_max_light(args.hklI_folder, args.data_name, args.folder)
