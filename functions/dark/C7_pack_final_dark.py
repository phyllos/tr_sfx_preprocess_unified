def pack_final_dark(callback, stream, record, folder_path, snapshot_folder_path,
                    summary_file_path, snapshot_prefix, max_file, red_file,
                    dataName="dark", dataForm="int", sortEventID=True,
                    remove_negative_pixels=False):
    import os
    import h5py
    import numpy as np
    from scipy import sparse
    from sparse_file_management import write_sparse

    callback("Packing final dark matrix...")
    base = os.path.splitext(os.path.basename(stream))[0] + "_PreProcessed_Data_0"
    index = 1
    directory_name = base
    while directory_name in os.listdir(folder_path):
        directory_name = base[:-1] + str(index); index += 1
    directory = os.path.join(folder_path, directory_name)
    os.mkdir(directory)
    record["C7_directory"] = directory

    with h5py.File(max_file, "r") as h5:
        h_max = int(h5["h_max"][()]); k_max = int(h5["k_max"][()]); l_max = int(h5["l_max"][()])
    snapshot_info = np.atleast_2d(np.loadtxt(summary_file_path))
    if sortEventID:
        snapshot_info = snapshot_info[np.argsort(snapshot_info[:, 1], kind="stable")]
    num_snapshots = snapshot_info.shape[0]
    sort_notice = "data sorted based on serial number" if sortEventID else "data NOT sorted"
    with h5py.File(red_file, "r") as h5:
        redundancy = h5["redundancy"][:]

    active = np.flatnonzero(redundancy.T.flatten() > 0)
    num_unique = active.size
    num_h, num_k, num_l = h_max+1, k_max+1, l_max+1
    grid_h, grid_k, grid_l = np.meshgrid(
        np.arange(num_h), np.arange(num_k), np.arange(num_l), indexing="ij"
    )
    T = np.zeros((num_snapshots, num_unique), dtype=float)
    M = np.zeros((num_snapshots, num_unique), dtype=float)
    for row_index, row in enumerate(snapshot_info):
        run_id, event_id = map(int, row[:2])
        temp = np.zeros((num_h, num_k, num_l), dtype=float)
        count = np.zeros_like(temp)
        path = os.path.join(snapshot_folder_path, f"{snapshot_prefix}_{run_id}_{event_id}_hklI.dat")
        with open(path, "r", encoding="utf-8") as snapshot:
            for line in snapshot:
                h, k, l = map(int, line.split()[:3]); intensity = float(line.split()[3])
                temp[h, k, l] += intensity; count[h, k, l] += 1
        count_vector = count.T.flatten()
        M[row_index] = count_vector[active] > 0
        count_vector[count_vector == 0] = 1
        T[row_index] = (temp.T.flatten() / count_vector)[active]

    miller_h = grid_h.T.flatten()[active]
    miller_k = grid_k.T.flatten()[active]
    miller_l = grid_l.T.flatten()[active]
    T = sparse.csr_matrix(T); M = sparse.csr_matrix(M)
    if remove_negative_pixels:
        negative = T.data < 0
        T.data[negative] = 0
        T.eliminate_zeros()
        notice_negative = "negative pixels set to zero"
    else:
        notice_negative = "negative pixels survived"
    if str(dataForm).lower().startswith("amp"):
        T.data = np.sqrt(np.maximum(T.data, 0))

    export_name = f"{dataName}_{dataForm}_sortEvent_nS{num_snapshots}_nBrg{num_unique}.hdf5"
    export_path = os.path.join(directory, export_name)
    with h5py.File(export_path, "w") as h5:
        write_sparse(T, "T", h5); write_sparse(M, "M", h5)
        for name, value in {
            "miller_h": miller_h, "miller_k": miller_k, "miller_l": miller_l,
            "sort_notice": sort_notice, "notice_negative_pix": notice_negative,
            "redundancy": redundancy, "active_reflection": active,
        }.items():
            h5.create_dataset(name, data=np.bytes_(value) if isinstance(value, str) else value)

    # Legacy driver passes the record dictionary as the second argument.
    record["C7_directory"] = directory
    record["C7_file"] = export_path
    return export_path
