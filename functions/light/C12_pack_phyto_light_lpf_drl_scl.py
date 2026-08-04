import os
import argparse
import h5py
import numpy as np
from sparse_file_management import read_sparse, write_sparse, copy_if_exists


def _output_name(input_file, suffix):
    folder = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(folder, f'{stem}_{suffix}.hdf5')


def pack_phyto_light_lpf_drl_scl(input_file, output_file=None, a=54.95, b=116.5, c=117.7, generate_hkl_avg=True):
    """C12: scale by partialator OSF and relB."""
    if output_file is None:
        output_file = _output_name(input_file, 'SCL')
    with h5py.File(input_file, 'r') as fin:
        T = read_sparse(fin, 'T_lpf_drl').tocoo()
        M_drl = read_sparse(fin, 'M_drl')
        h = np.asarray(fin['miller_h'][()]).squeeze()
        k = np.asarray(fin['miller_k'][()]).squeeze()
        l = np.asarray(fin['miller_l'][()]).squeeze()
        OSF = np.asarray(fin['OSF'][()]).squeeze()
        relB = np.asarray(fin['relB'][()]).squeeze()
        q2 = (h / a) ** 2 + (k / b) ** 2 + (l / c) ** 2
        scale = np.exp(-OSF[T.row]) * np.exp(relB[T.row] * q2[T.col] / 4.0)
        T_scl = T.copy()
        T_scl.data = T.data * scale
        T_scl = T_scl.tocsc()

        with h5py.File(output_file, 'w') as fout:
            write_sparse(fout, 'T_lpf_drl_scl', T_scl)
            write_sparse(fout, 'M_drl', M_drl)
            for name in ['miller_h', 'miller_k', 'miller_l', 'delay', 'DRL', 'LPF', 'runID', 'eventID',
                         'idx', 'idx0', 'id_unif', 'id_unif0', 'indSort_delay', 'ind_delay_uniform', 'ind_delay_uniform0']:
                if name in fin:
                    fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze())
            copy_if_exists(fin, fout, ['sort_notice', 'notice_negative_pix', 'noticeDRL'])
            fout.create_dataset('noticeSCL', data=np.bytes_('Data scaled by partialator parameters'))

    if generate_hkl_avg:
        hkl_file = os.path.splitext(output_file)[0] + '_AVG.hkl'
        counts = np.asarray(M_drl.sum(axis=0)).ravel()
        sums = np.asarray(T_scl.sum(axis=0)).ravel()
        avg = np.divide(sums, counts, out=np.zeros_like(sums, dtype=float), where=counts != 0)
        avg[~np.isfinite(avg)] = 0
        avg[avg < 0] = 0
        std_new = np.sqrt(avg)
        np.savetxt(hkl_file, np.column_stack([h, k, l, avg, std_new]), fmt='%6d %6d %6d %12.2f %12.2f')
        print(f'Saved {hkl_file}')
    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    p.add_argument('--no-hkl-avg', action='store_true')
    args = p.parse_args()
    pack_phyto_light_lpf_drl_scl(args.input_file, args.output, generate_hkl_avg=not args.no_hkl_avg)
