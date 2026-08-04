import os
import argparse
import h5py
import numpy as np
from sparse_file_management import read_sparse, write_sparse, copy_if_exists


def _output_name(input_file, suffix):
    folder = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(folder, f'{stem}_{suffix}.hdf5')


def pack_phyto_light_lpf_drl_scl_bst(input_file, output_file=None):
    """C13: boost by dividing each Bragg-reflection column by multiplicity count."""
    if output_file is None:
        output_file = _output_name(input_file, 'BST')
    with h5py.File(input_file, 'r') as fin:
        T = read_sparse(fin, 'T_lpf_drl_scl')
        M = read_sparse(fin, 'M_drl')
        counts = np.asarray(M.sum(axis=0)).ravel().astype(float)
        inv_counts = np.divide(1.0, counts, out=np.zeros_like(counts), where=counts != 0)
        T_bst = T.multiply(inv_counts.reshape(1, -1)).tocsc()
        with h5py.File(output_file, 'w') as fout:
            write_sparse(fout, 'T_lpf_drl_scl_bst', T_bst)
            write_sparse(fout, 'M_drl', M)
            for name in ['miller_h', 'miller_k', 'miller_l', 'delay', 'DRL', 'LPF', 'runID', 'eventID',
                         'idx', 'idx0', 'id_unif', 'id_unif0', 'indSort_delay', 'ind_delay_uniform', 'ind_delay_uniform0']:
                if name in fin:
                    fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze())
            copy_if_exists(fin, fout, ['sort_notice', 'notice_negative_pix'])
            fout.create_dataset('noticeBST', data=np.bytes_('boosting applied to T_lpf_drl_scl'))
    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    args = p.parse_args()
    pack_phyto_light_lpf_drl_scl_bst(args.input_file, args.output)
