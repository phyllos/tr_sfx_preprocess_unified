def pack_allInfo_dark(callback, params_summ, stream_sum, summary_file,
                      main_folder, output, dataType="dark"):
    import os
    import h5py
    import numpy as np

    callback("Merging params and stream data...")
    with h5py.File(stream_sum, "r") as h5:
        drl = h5["DRL"][:]; stream_serial = h5["nSer"][:]; n_refl = h5["nRefl"][:]
    with h5py.File(params_summ, "r") as h5:
        params_serial = h5["nSer"][:]; osf = h5["OSF"][:]; rel_b = h5["relB"][:]

    _, stream_idx, params_idx = np.intersect1d(stream_serial, params_serial, return_indices=True)
    stream_idx = np.sort(stream_idx); params_idx = np.sort(params_idx)
    serial = params_serial[params_idx]
    drl = drl[stream_idx]; n_refl = n_refl[stream_idx]
    osf = osf[params_idx]; rel_b = rel_b[params_idx]

    snapshot = np.atleast_2d(np.loadtxt(summary_file))
    _, snap_idx, meta_idx = np.intersect1d(snapshot[:, 1], serial, return_indices=True)
    snap_idx = np.sort(snap_idx); meta_idx = np.sort(meta_idx)
    serial = serial[meta_idx]; n_refl = n_refl[meta_idx]; drl = drl[meta_idx]
    osf = osf[meta_idx]; rel_b = rel_b[meta_idx]
    snapshot = snapshot[snap_idx]
    np.savetxt(summary_file, snapshot.astype(int), fmt="%15d %15d %15d")

    notice = "parameters NOT sorted based on eventID yet."
    output_name = os.path.join(main_folder, f"merged_snapshotInfo_{dataType}_allInfo.hdf5")
    with h5py.File(output_name, "w") as h5:
        for name, value in zip(
            ["SerNo", "nBrg", "DRL", "OSF", "relB", "notice"],
            [serial, n_refl, drl, osf, rel_b, notice],
        ):
            h5.create_dataset(name, data=np.bytes_(value) if isinstance(value, str) else value)
    output["C6_file"] = output_name
    np.savetxt(
        os.path.join(main_folder, f"merged_snapshotInfo_{dataType}_allInfo.dat"),
        np.column_stack([serial, n_refl, drl, osf, rel_b]),
        fmt="%6d %6d %12.2f %12.2f %12.2f",
    )
