import os
import re
import argparse
import h5py
import numpy as np


def _chunks(lines):
    chunk = []
    in_chunk = False
    for line in lines:
        if 'Begin chunk' in line:
            chunk = [line]
            in_chunk = True
        elif 'End chunk' in line and in_chunk:
            chunk.append(line)
            yield chunk
            chunk = []
            in_chunk = False
        elif in_chunk:
            chunk.append(line)


def _search(pattern, text, cast=float):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else None


def read_stream_files_light(stream_file, data_name, folder_path='.'):
    """Read SACLA light-data .stream file.

    Output columns: nRun, nEvent, nRefl, DRL. Indexed_by=none chunks are skipped.
    """
    stream_file = os.path.abspath(stream_file)
    with open(stream_file, 'r', errors='ignore') as f:
        lines = f.readlines()

    nRun, nEvent, nRefl, DRL = [], [], [], []
    for ch in _chunks(lines):
        text = ''.join(ch)
        m_index = re.search(r'indexed_by\s*=\s*(\S+)', text)
        if m_index and m_index.group(1).lower() == 'none':
            continue
        run = _search(r'run(\d+)', text, int)
        event = _search(r'tag-?(\d+)', text, int)
        refl = _search(r'num_reflections\s*=\s*(\d+)', text, int)
        drl = _search(r'diffraction_resolution_limit\s*=\s*([0-9.]+)', text, float)
        if None in (run, event, refl, drl):
            continue
        nRun.append(run); nEvent.append(event); nRefl.append(refl); DRL.append(drl)

    nRun = np.asarray(nRun, dtype=np.int64)
    nEvent = np.asarray(nEvent, dtype=np.int64)
    nRefl = np.asarray(nRefl, dtype=np.int64)
    DRL = np.asarray(DRL, dtype=np.float64)

    os.makedirs(folder_path, exist_ok=True)
    out_h5 = os.path.join(folder_path, f'merged_snapshotInfo_phyto_{data_name}.hdf5')
    out_dat = os.path.join(folder_path, f'merged_snapshotInfo_phyto_{data_name}.dat')
    with h5py.File(out_h5, 'w') as h5:
        h5.create_dataset('nRun', data=nRun)
        h5.create_dataset('nEvent', data=nEvent)
        h5.create_dataset('nRefl', data=nRefl)
        h5.create_dataset('DRL', data=DRL)
    np.savetxt(out_dat, np.column_stack([nRun, nEvent, nRefl, DRL]),
               fmt='%12d %16d %8d %10.4f')
    print(f'Saved {out_h5}')
    print(f'Saved {out_dat}')
    return out_h5


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stream_file')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    args = p.parse_args()
    read_stream_files_light(args.stream_file, args.data_name, args.folder)
