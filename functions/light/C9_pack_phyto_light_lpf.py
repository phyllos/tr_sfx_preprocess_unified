import os
import re
import argparse
import h5py
import numpy as np
from sparse_file_management import read_sparse, write_sparse, copy_if_exists


def _output_name(input_file, suffix):
    folder = os.path.dirname(os.path.abspath(input_file))
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return os.path.join(folder, f'{stem}_{suffix}.hdf5')


def pack_phyto_light_lpf(input_file, output_file=None, a=54.95, b=116.5, c=117.7, wavelength=1.77):
    """C9: divide Bragg intensities by Lorentz-polarization factor."""
    if output_file is None:
        output_file = _output_name(input_file, 'LPF')
    with h5py.File(input_file, 'r') as fin:
        T = read_sparse(fin, 'T')
        M = read_sparse(fin, 'M')
        h = np.asarray(fin['miller_h'][()]).squeeze()
        k = np.asarray(fin['miller_k'][()]).squeeze()
        l = np.asarray(fin['miller_l'][()]).squeeze()
        q2 = (h / a) ** 2 + (k / b) ** 2 + (l / c) ** 2
        q = np.sqrt(q2)
        sin_theta = wavelength * q / 2.0
        cos_2theta = 1.0 - 2.0 * sin_theta ** 2
        LPF = (1.0 + cos_2theta ** 2) / 2.0
        LPF[LPF == 0] = 1.0
        T_lpf = T.multiply(1.0 / LPF.reshape(1, -1)).tocsc()

        with h5py.File(output_file, 'w') as fout:
            write_sparse(fout, 'T_lpf', T_lpf)
            write_sparse(fout, 'M', M)
            for name in ['miller_h', 'miller_k', 'miller_l', 'delay', 'DRL', 'OSF', 'relB', 'runID', 'eventID',
                         'idx', 'idx0', 'id_unif', 'id_unif0', 'indSort_delay', 'ind_delay_uniform', 'ind_delay_uniform0']:
                if name in fin:
                    fout.create_dataset(name, data=np.asarray(fin[name][()]).squeeze())
            copy_if_exists(fin, fout, ['sort_notice', 'notice_negative_pix'])
            fout.create_dataset('LPF', data=LPF)
            fout.create_dataset('noticeLPF', data=np.bytes_('Bragg intensities divided by Polarization factor'))
    print(f'Saved {output_file}')
    return output_file


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default=None)
    args = p.parse_args()
    pack_phyto_light_lpf(args.input_file, args.output)
