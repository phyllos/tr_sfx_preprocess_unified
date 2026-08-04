import os
import argparse
import h5py
import numpy as np
from sparse_file_management import read_sparse, write_sparse, copy_if_exists


def _output_name(input_file, suffix):
    folder = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(folder, f'{stem}_{suffix}.hdf5')


def pack_phyto_light_lpf_drl(input_file, output_file=None, mask_file=None):
    """C11: apply DRL mask if provided; otherwise use MATLAB test behavior maskDRL=ones."""
    if output_file is None:
        output_file = _output_name(input_file, 'DRL')
    with h5py.File(input_file, 'r') as fin:
        T_lpf = read_sparse(fin, 'T_lpf')
        M = read_sparse(fin, 'M')
        if mask_file is None:
            M_drl = M
            T_lpf_drl = T_lpf
            notice = 'Bragg reflections beyond DRL NOT removed: maskDRL = ones(nS,nBrg)'
        else:
            with h5py.File(mask_file, 'r') as fm:
                maskDRL = read_sparse(fm, 'maskDRL')
            M_drl = M.multiply(maskDRL).tocsc()
            T_lpf_drl = T_lpf.multiply(M_drl).tocsc()
            notice = 'Bragg reflections beyond DRLs are removed, and qmax is q at DRL.'

        with h5py.File(output_file, 'w') as fout:
            write_sparse(fout, 'T_lpf_drl', T_lpf_drl)
            write_sparse(fout, 'M_drl', M_drl)
            for name in ['miller_h', 'miller_k', 'miller_l', 'delay', 'DRL', 'LPF', 'OSF', 'relB', 'runID', 'eventID',
                         'idx', 'idx0', 'id_unif', 'id_unif0', 'indSort_delay', 'ind_delay_uniform', 'ind_delay_uniform0']:
                if name in fin:
                    fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze())
            copy_if_exists(fin, fout, ['sort_notice', 'notice_negative_pix'])
            fout.create_dataset('noticeDRL', data=np.bytes_(notice))
    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    p.add_argument('--mask-file', default=None)
    args = p.parse_args()
    pack_phyto_light_lpf_drl(args.input_file, args.output, args.mask_file)
