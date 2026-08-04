def read_partialator_params(callback, params_file, folder_path, output_to):
    import os
    import h5py
    import numpy as np

    callback("Parsing parameters...")
    directory = "PARAMETERS_0"
    index = 1
    while directory in os.listdir(folder_path):
        directory = f"PARAMETERS_{index}"
        index += 1
    directory = os.path.join(folder_path, directory)
    os.mkdir(directory)
    output_to["C1_directory"] = directory

    serial, osf, rel_b = [], [], []
    with open(params_file, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            fields = line.strip().split()
            if not fields:
                continue
            try:
                if len(fields) == 3:
                    event = float(fields[0])
                else:
                    event = float(fields[6][4:-2])
                serial.append(event)
                osf.append(float(fields[1]))
                rel_b.append(float(fields[2]))
            except (ValueError, IndexError):
                continue

    output_name = os.path.join(
        directory,
        f"partialator_params_{os.path.splitext(os.path.basename(params_file))[0]}.hdf5",
    )
    with h5py.File(output_name, "w") as h5:
        h5.create_dataset("nSer", data=np.asarray(serial))
        h5.create_dataset("OSF", data=np.asarray(osf))
        h5.create_dataset("relB", data=np.asarray(rel_b))
    output_to["C1_file"] = output_name
