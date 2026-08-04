import os
import re
import argparse
import h5py
import numpy as np
from sparse_file_management import read_sparse, write_sparse, copy_if_exists


def _parse_nbrg(stem):
    m = re.search(r'nBrg(\d+)', stem)
    return m.group(1) if m else None


def _output_name(input_file, nS):
    folder = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    prefix = stem.split('_nS')[0] if '_nS' in stem else stem
    nBrg = _parse_nbrg(stem)
    if nBrg:
        return os.path.join(folder, f'{prefix}_unifdelay_nS{nS}_nBrg{nBrg}.hdf5')
    return os.path.join(folder, f'{prefix}_unifdelay_nS{nS}.hdf5')


def generate_uniform_delay_sacla2021_hdf5(input_file, output_file=None, ss=155, tmin=-84, tmax=550, seed=None):
    """C8: keep at most ss snapshots per unique delay bin in tmin < delay < tmax."""
    rng = np.random.default_rng(seed)
    with h5py.File(input_file, 'r') as fin:
        delay0 = np.asarray(fin['delay'][()]).squeeze()
        idx0 = np.flatnonzero((delay0 < tmax) & (delay0 > tmin))
        delay = delay0[idx0]

        selected = []
        for d in np.unique(delay):
            rows = np.flatnonzero(delay == d)
            keep = min(ss, rows.size)
            chosen = rng.choice(rows, size=keep, replace=False)
            selected.append(np.sort(chosen))
        id_unif0 = np.concatenate(selected) if selected else np.array([], dtype=np.int64)
        final_rows0 = idx0[id_unif0]
        nS = len(final_rows0)

        if output_file is None:
            output_file = _output_name(input_file, nS)

        T = read_sparse(fin, 'T')[final_rows0, :].tocsc()
        M = read_sparse(fin, 'M')[final_rows0, :].tocsc()

        with h5py.File(output_file, 'w') as fout:
            write_sparse(fout, 'T', T)
            write_sparse(fout, 'M', M)
            for name in ['delay', 'DRL', 'runID', 'eventID', 'indSort_delay', 'OSF', 'relB']:
                if name in fin:
                    fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze()[final_rows0])
            for name in ['miller_h', 'miller_k', 'miller_l']:
                fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze())
            copy_if_exists(fin, fout, ['sort_notice', 'notice_negative_pix'])
            fout.create_dataset('idx', data=idx0 + 1)                         # MATLAB-style 1-based
            fout.create_dataset('idx0', data=idx0)                            # Python 0-based
            fout.create_dataset('id_unif', data=id_unif0 + 1)                 # index within time-window subset, 1-based
            fout.create_dataset('id_unif0', data=id_unif0)
            fout.create_dataset('ind_delay_uniform', data=final_rows0 + 1)     # original C7 row index, 1-based
            fout.create_dataset('ind_delay_uniform0', data=final_rows0)
            fout.attrs['ss'] = int(ss)
            fout.attrs['tmin'] = float(tmin)
            fout.attrs['tmax'] = float(tmax)
            fout.attrs['seed'] = -1 if seed is None else int(seed)

    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    p.add_argument('--ss', type=int, default=155)
    p.add_argument('--tmin', type=float, default=-84)
    p.add_argument('--tmax', type=float, default=550)
    p.add_argument('--seed', type=int, default=None)
    args = p.parse_args()
    generate_uniform_delay_sacla2021_hdf5(args.input_file, args.output, args.ss, args.tmin, args.tmax, args.seed)
