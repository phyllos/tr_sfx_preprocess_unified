def read_stream_files(stream_file, data_name, folder_path, directory, output_to,
                      dataType="dark", paramsExists=False):
    import os
    import h5py
    import numpy as np

    directory = os.path.join(folder_path, directory)
    with open(stream_file, "r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()

    starts = [i for i, line in enumerate(lines) if "Begin chunk" in line]
    chunks = [lines[starts[i]: starts[i+1]] for i in range(len(starts)-1)]
    if starts:
        chunks.append(lines[starts[-1]:])

    serial, n_refl, drl = [], [], []
    dat_path = os.path.join(directory, f"merged_snapshot_info_{data_name}_{dataType}.dat")
    with open(dat_path, "w", encoding="utf-8") as output:
        for chunk in chunks:
            event_line = None
            indexed = True
            refl = resolution = None
            for line in chunk:
                if "Event:" in line:
                    event_line = line
                elif "indexed_by" in line and line.split()[-1] == "none":
                    indexed = False
                    break
                elif "num_reflections" in line:
                    refl = int(line.split()[-1])
                elif "diffraction_resolution_limit" in line:
                    resolution = float(line.split()[2])
                elif "Reflections measured after indexing" in line:
                    if indexed and event_line is not None and refl is not None and resolution is not None:
                        event_text = event_line.split("-")[-1].splitlines()[0]
                        event = int(event_text[:-2])
                        serial.append(event); n_refl.append(refl); drl.append(resolution)
                        print(f"{event:10d} {refl:10d} {resolution:10f}", file=output)

    h5_path = os.path.join(directory, f"merged_snapshot_info_{data_name}_{dataType}.hdf5")
    with h5py.File(h5_path, "w") as h5:
        h5.create_dataset("nSer", data=serial)
        h5.create_dataset("DRL", data=drl)
        h5.create_dataset("nRefl", data=n_refl)
    output_to["C2_file"] = h5_path

    if not paramsExists:
        with h5py.File(os.path.join(directory, "params_ones.hdf5"), "w") as h5:
            h5.create_dataset("nSer", data=np.asarray(serial))
            h5.create_dataset("OSF", data=np.ones(len(serial)))
            h5.create_dataset("relB", data=np.zeros(len(serial)))
