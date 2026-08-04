def pack_dark_scl(callback, main_folder, C7_file, pack_final_dark_file,
                  a, b, c, output_to, dataName="dark", dataForm="int",
                  generate_hkl_avg=True, remove_negative_pixels=False):
    import os
    import h5py
    import numpy as np
    from scipy import sparse
    from sparse_file_management import load_sparse, write_sparse

    callback("Applying scaling parameters...")
    with h5py.File(pack_final_dark_file, "r") as meta, h5py.File(C7_file, "r") as packed:
        h = packed["miller_h"][:]; k = packed["miller_k"][:]; l = packed["miller_l"][:]
        osf = meta["OSF"][:].astype(float); rel_b = meta["relB"][:].astype(float)
        T = load_sparse("T", packed).toarray(); M = load_sparse("M", packed)
        qx = h / a
        qy = h / (np.sqrt(3.0)*a) + 2.0*k / (np.sqrt(3.0)*b)
        qz = l / c
        q2 = qx*qx + qy*qy + qz*qz
        osf[osf != 0] = 1.0 / osf[osf != 0]
        osf[~np.isfinite(osf)] = 1.0; osf = np.minimum(osf, 55)
        rel_b = np.clip(rel_b, -500, 500)
        if T.shape[0] != osf.size:
            raise ValueError(f"C7 rows ({T.shape[0]}) do not match OSF rows ({osf.size}).")
        T_scl = sparse.csr_matrix(T * osf[:, None] * np.exp(np.outer(rel_b, q2 / 4.0)))
        notice = "Data scaled by partialator parameters"
        h5_name = f"data_{dataName}_{dataForm}_sortEvent_scl_nS{T.shape[0]}_nBrg{T.shape[1]}.hdf5"
        h5_path = os.path.join(main_folder, h5_name)
        with h5py.File(h5_path, "w") as out:
            write_sparse(T_scl, "T_scl", out)
            for name, value in {
                "miller_h": h, "miller_k": k, "miller_l": l,
                "noticeSCL": notice,
                "sort_notice": packed["sort_notice"][()],
                "notice_negative_pix": packed["notice_negative_pix"][()],
            }.items():
                out.create_dataset(name, data=np.bytes_(value) if isinstance(value, str) else value)
        output_to["C8_hdf5_file"] = h5_path

        if generate_hkl_avg:
            values = np.asarray(T_scl.sum(axis=0)).ravel()
            counts = np.asarray(M.sum(axis=0)).ravel()
            valid = counts != 0
            values[valid] /= counts[valid]
            values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            if remove_negative_pixels:
                values[values < 0] = 0
            sigma = np.sqrt(np.maximum(values, 0))
            hkl_name = f"data_{dataName}_{dataForm}_sortEvent_scl_avg_nS{T.shape[0]}_nBrg{T.shape[1]}.hkl"
            hkl_path = os.path.join(main_folder, hkl_name)
            np.savetxt(hkl_path, np.column_stack([h, k, l, values, sigma]),
                       fmt="%6d %6d %6d %13.2f %12.2f")
            output_to["C8_hkl_file"] = hkl_path
    return h5_path
