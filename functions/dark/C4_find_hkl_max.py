def find_hkl_max(callback, snapshot_folder_path, summary_file, snapshot_prefix,
                 main_folder, output_to):
    import os
    import h5py

    callback("Finding min/max...")
    h_max = k_max = l_max = -float("inf")
    num_snapshots = 0
    with open(summary_file, "r", encoding="utf-8") as summary:
        for summary_line in summary:
            run_id, event_id, _ = summary_line.split()
            num_snapshots += 1
            path = os.path.join(snapshot_folder_path, f"{snapshot_prefix}_{run_id}_{event_id}_hklI.dat")
            with open(path, "r", encoding="utf-8") as snapshot:
                for line in snapshot:
                    fields = line.split()
                    if len(fields) < 3:
                        continue
                    h, k, l = map(int, fields[:3])
                    h_max = max(h_max, h); k_max = max(k_max, k); l_max = max(l_max, l)
    output_name = os.path.join(main_folder, "max_vals.hdf5")
    with h5py.File(output_name, "w") as h5:
        h5.create_dataset("h_max", data=int(h_max))
        h5.create_dataset("k_max", data=int(k_max))
        h5.create_dataset("l_max", data=int(l_max))
        h5.create_dataset("num_snapshots", data=num_snapshots)
    output_to["C4_file"] = output_name
