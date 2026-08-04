def pack_phyto_dark_bst(callback, scl_vars, unscl_vars, output_to,
                        folder_path, dataName="dark", dataForm="int"):
    import os
    import h5py
    import numpy as np
    from sparse_file_management import load_sparse, write_sparse

    callback("Boosting matrix...")
    with h5py.File(scl_vars, "r") as scaled, h5py.File(unscl_vars, "r") as unscaled:
        T_scl = load_sparse("T_scl", scaled)
        M = load_sparse("M", unscaled)
        counts = np.asarray(M.sum(axis=0)).ravel()
        inverse = np.zeros_like(counts, dtype=float)
        inverse[counts != 0] = 1.0 / counts[counts != 0]
        T_bst = T_scl.multiply(inverse).tocsr()
        nS, nBrg = T_scl.shape
        path = os.path.join(folder_path, f"data_{dataName}_{dataForm}_sortEvent_scl_bst_nS{nS}_nBrg{nBrg}.hdf5")
        with h5py.File(path, "w") as out:
            write_sparse(T_bst, "T_bst", out); write_sparse(T_scl, "T_scl", out); write_sparse(M, "M", out)
            for name in ["miller_h", "miller_k", "miller_l", "sort_notice", "notice_negative_pix"]:
                if name in scaled:
                    out.create_dataset(name, data=scaled[name][()])
            out.create_dataset("noticeBST", data=np.bytes_("boosting applied to T_scl"))
    output_to["C9_file"] = path
    return path
