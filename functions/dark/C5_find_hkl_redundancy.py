import numpy as np


def find_hkl_redundancy(callback, snapshot_folder_path, summary_file,
                        snapshot_prefix, home, max_file, output):
    import os
    import h5py

    callback("Generating redundancy...")
    with h5py.File(max_file, "r") as h5:
        h_max = int(h5["h_max"][()]); k_max = int(h5["k_max"][()]); l_max = int(h5["l_max"][()])
    redundancy = np.zeros((h_max+1, k_max+1, l_max+1), dtype=np.int64)
    with open(summary_file, "r", encoding="utf-8") as summary:
        for line in summary:
            run_id, event_id, _ = line.split()
            path = os.path.join(snapshot_folder_path, f"{snapshot_prefix}_{run_id}_{event_id}_hklI.dat")
            with open(path, "r", encoding="utf-8") as snapshot:
                for row in snapshot:
                    h, k, l = map(int, row.split()[:3])
                    redundancy[h, k, l] += 1
    output_name = os.path.join(home, "redundancy.hdf5")
    with h5py.File(output_name, "w") as h5:
        h5.create_dataset("redundancy", data=redundancy)
    output["C5_file"] = output_name
