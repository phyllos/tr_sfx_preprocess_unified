import os
import argparse
import h5py
import numpy as np
import scipy.io as sio


def _load_h5_vectors(path, names):
    with h5py.File(path, 'r') as h5:
        return [np.asarray(h5[n][()]).squeeze() for n in names]


def _load_delay_file(path, data_name):
    # Your upto1ps data uses delay_1ps/tag_1ps in delays_original.mat.
    suffix = '1ps' if data_name in ('upto1ps', '1ps') else data_name
    try:
        mat = sio.loadmat(path)
        keys = {k: v for k, v in mat.items() if not k.startswith('__')}
        delay_key = f'delay_{suffix}' if f'delay_{suffix}' in keys else 'delay'
        tag_key = f'tag_{suffix}' if f'tag_{suffix}' in keys else 'tag'
        if delay_key not in keys or tag_key not in keys:
            raise KeyError(f'Could not find delay/tag for suffix {suffix}. Keys: {list(keys)}')
        return np.asarray(keys[delay_key]).squeeze(), np.asarray(keys[tag_key]).squeeze()
    except NotImplementedError:
        with h5py.File(path, 'r') as h5:
            delay_key = f'delay_{suffix}' if f'delay_{suffix}' in h5 else 'delay'
            tag_key = f'tag_{suffix}' if f'tag_{suffix}' in h5 else 'tag'
            return np.asarray(h5[delay_key][()]).squeeze(), np.asarray(h5[tag_key][()]).squeeze()


def pack_phyto_allInfo_light(stream_info_h5, params_h5, delays_mat, data_name, folder_path='.'):
    """Merge stream info, partialator params, and delay file.

    Output columns: runID, eventID, nBrg, DRL, delay, OSF, relB.
    """
    nR1, nE1, nRefl, DRL = _load_h5_vectors(stream_info_h5, ['nRun', 'nEvent', 'nRefl', 'DRL'])
    nRun, nEvent, OSF, relB = _load_h5_vectors(params_h5, ['nRun', 'nEvent', 'OSF', 'relB'])

    if len(nR1) != len(nRun) or np.any(nR1 != nRun) or np.any(nE1 != nEvent):
        print('Warning: stream and params run/event arrays are not identical; matching by eventID.')

    delay_all, tag_all = _load_delay_file(delays_mat, data_name)
    delay_by_tag = {int(t): float(d) for t, d in zip(tag_all, delay_all)}

    rows = []
    for run, event, nrefl, drl, osf, rb in zip(nRun, nEvent, nRefl, DRL, OSF, relB):
        event_int = int(event)
        if event_int in delay_by_tag:
            rows.append((int(run), event_int, int(nrefl), float(drl), delay_by_tag[event_int], float(osf), float(rb)))

    info = np.asarray(rows, dtype=np.float64)
    if info.size == 0:
        raise RuntimeError('No common eventID/tag found between params/stream and delay file.')

    runID = info[:, 0].astype(np.int64)
    eventID = info[:, 1].astype(np.int64)
    nBrg = info[:, 2].astype(np.int64)
    DRL = info[:, 3]
    delay = info[:, 4]
    OSF = info[:, 5]
    relB = info[:, 6]

    os.makedirs(folder_path, exist_ok=True)
    out_h5 = os.path.join(folder_path, f'merged_snapshotInfo_phyto_{data_name}_allInfo.hdf5')
    out_dat = os.path.join(folder_path, f'merged_snapshotInfo_phyto_{data_name}_allInfo.dat')

    with h5py.File(out_h5, 'w') as h5:
        h5.create_dataset('runID', data=runID)
        h5.create_dataset('eventID', data=eventID)
        h5.create_dataset('nBrg', data=nBrg)
        h5.create_dataset('DRL', data=DRL)
        h5.create_dataset('delay', data=delay)
        h5.create_dataset('OSF', data=OSF)
        h5.create_dataset('relB', data=relB)
        h5.create_dataset('notice', data=np.bytes_('parameters NOT sorted based on delay yet'))

    np.savetxt(out_dat, np.column_stack([runID, eventID, nBrg, DRL, delay, OSF, relB]),
               fmt='%12d %16d %8d %10.4f %12.4f %12.6f %12.6f')
    print(f'Saved {out_h5}')
    print(f'Saved {out_dat}')
    return out_h5


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stream_info_h5')
    p.add_argument('params_h5')
    p.add_argument('delays_mat')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    args = p.parse_args()
    pack_phyto_allInfo_light(args.stream_info_h5, args.params_h5, args.delays_mat, args.data_name, args.folder)
