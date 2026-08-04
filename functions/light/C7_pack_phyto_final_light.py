import os
import argparse
import h5py
import numpy as np
from scipy import sparse
from sparse_file_management import write_sparse


def pack_phyto_final_light(allInfo_dat, redundancy_h5, hklI_folder, data_name, folder_path='.', remove_negative_pixels=False):
    """Pack light-data hklI files into sparse T and M matrices, sorted by delay."""
    info = np.loadtxt(allInfo_dat, ndmin=2)
    indSort_delay0 = np.argsort(info[:, 4], kind='mergesort')
    info = info[indSort_delay0]

    runID = info[:, 0].astype(np.int64)
    eventID = info[:, 1].astype(np.int64)
    nRefl = info[:, 2].astype(np.int64)
    DRL = info[:, 3]
    delay = info[:, 4]
    OSF = info[:, 5]
    relB = info[:, 6]

    with h5py.File(redundancy_h5, 'r') as h5:
        redundancy = np.asarray(h5['redundancy'][()])
    h_grid, k_grid, l_grid = np.meshgrid(
        np.arange(redundancy.shape[0]),
        np.arange(redundancy.shape[1]),
        np.arange(redundancy.shape[2]),
        indexing='ij'
    )
    active = redundancy.reshape(-1, order='F') > 0
    miller_h = h_grid.reshape(-1, order='F')[active]
    miller_k = k_grid.reshape(-1, order='F')[active]
    miller_l = l_grid.reshape(-1, order='F')[active]
    hkl_to_col = {(int(h), int(k), int(l)): i for i, (h, k, l) in enumerate(zip(miller_h, miller_k, miller_l))}

    rows, cols, vals = [], [], []
    m_rows, m_cols = [], []
    for i, (run, event) in enumerate(zip(runID, eventID)):
        fn = os.path.join(hklI_folder, f'sacla2021_run{int(run)}_tag{int(event)}_hklI.dat')
        if not os.path.exists(fn):
            continue
        arr = np.loadtxt(fn, ndmin=2)
        for h, k, l, inten in arr[:, :4]:
            key = (int(h), int(k), int(l))
            col = hkl_to_col.get(key)
            if col is None:
                continue
            inten = float(inten)
            if remove_negative_pixels and inten < 0:
                inten = 0.0
            rows.append(i); cols.append(col); vals.append(inten)
            m_rows.append(i); m_cols.append(col)

    nS = len(runID)
    nBrg = len(miller_h)
    T = sparse.coo_matrix((vals, (rows, cols)), shape=(nS, nBrg)).tocsc()
    M = sparse.coo_matrix((np.ones(len(m_rows)), (m_rows, m_cols)), shape=(nS, nBrg)).tocsc()

    os.makedirs(folder_path, exist_ok=True)
    out = os.path.join(folder_path, f'dataPhyto_{data_name}_int_sortdelay_nS{nS}_nBrg{nBrg}.hdf5')
    with h5py.File(out, 'w') as h5:
        write_sparse(h5, 'T', T)
        write_sparse(h5, 'M', M)
        for name, arr in [('miller_h', miller_h), ('miller_k', miller_k), ('miller_l', miller_l),
                          ('delay', delay), ('DRL', DRL), ('OSF', OSF), ('relB', relB),
                          ('runID', runID), ('eventID', eventID)]:
            h5.create_dataset(name, data=np.asarray(arr).squeeze())
        h5.create_dataset('indSort_delay', data=indSort_delay0 + 1)  # MATLAB-style 1-based
        h5.create_dataset('sort_notice', data=np.bytes_('data sorted based on delay time'))
        h5.create_dataset('notice_negative_pix', data=np.bytes_('negative pixels kept' if not remove_negative_pixels else 'negative pixels set to zero'))
    print(f'Saved {out}')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('allInfo_dat')
    p.add_argument('redundancy_h5')
    p.add_argument('hklI_folder')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    p.add_argument('--remove-negative-pixels', action='store_true')
    args = p.parse_args()
    pack_phyto_final_light(args.allInfo_dat, args.redundancy_h5, args.hklI_folder,
                           args.data_name, args.folder, args.remove_negative_pixels)
