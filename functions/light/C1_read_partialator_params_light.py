import os
import re
import argparse
import h5py
import numpy as np


def read_partialator_params_light(params_file, folder_path='.', data_name=None):
    """Read SACLA light-data partialator .params file.

    Output columns: nRun, nEvent, OSF, relB.
    This follows the MATLAB C1 script but writes HDF5 + DAT.
    """
    params_file = os.path.abspath(params_file)
    if data_name is None:
        data_name = os.path.splitext(os.path.basename(params_file))[0]

    nRun, nEvent, OSF, relB = [], [], [], []
    with open(params_file, 'r', errors='ignore') as f:
        for line in f:
            parts = line.split()
            if len(parts) < 7:
                continue
            try:
                osf = float(parts[1])
                rb = float(parts[2])
            except ValueError:
                continue
            m_run = re.search(r'run(\d+)', line)
            m_tag = re.search(r'tag-?(\d+)', line)
            if not (m_run and m_tag):
                continue
            nRun.append(int(m_run.group(1)))
            nEvent.append(int(m_tag.group(1)))
            OSF.append(osf)
            relB.append(rb)

    nRun = np.asarray(nRun, dtype=np.int64)
    nEvent = np.asarray(nEvent, dtype=np.int64)
    OSF = np.asarray(OSF, dtype=np.float64)
    relB = np.asarray(relB, dtype=np.float64)

    os.makedirs(folder_path, exist_ok=True)
    out_h5 = os.path.join(folder_path, f'partialator_params_phyto_{data_name}.hdf5')
    out_dat = os.path.join(folder_path, f'partialator_params_phyto_{data_name}.dat')

    with h5py.File(out_h5, 'w') as h5:
        h5.create_dataset('nRun', data=nRun)
        h5.create_dataset('nEvent', data=nEvent)
        h5.create_dataset('OSF', data=OSF)
        h5.create_dataset('relB', data=relB)

    np.savetxt(out_dat, np.column_stack([nRun, nEvent, OSF, relB]),
               fmt='%12d %16d %14.6f %14.6f')
    print(f'Saved {out_h5}')
    print(f'Saved {out_dat}')
    return out_h5


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('params_file')
    p.add_argument('--folder', default='.')
    p.add_argument('--data-name', default=None)
    args = p.parse_args()
    read_partialator_params_light(args.params_file, args.folder, args.data_name)
