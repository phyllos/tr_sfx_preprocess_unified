def grab_DARK(callback, record, folder_path, stream_file, spacegroup, h_max, k_max, l_max):
    import os
    import time
    import numpy as np
    from hkl_symm_pyxtal_wyckoffs import get_hkl_asymm_table

    callback("Generating asymmetric unit...")
    table = get_hkl_asymm_table(spacegroup, h_max, k_max, l_max, positiveOctant=True)
    directory_name = "individual_snapshots_0"
    index = 1
    while directory_name in os.listdir(folder_path):
        directory_name = f"individual_snapshots_{index}"
        index += 1
    directory = os.path.join(folder_path, directory_name)
    os.mkdir(directory)

    summary_file = os.path.join(folder_path, f"snapshotInfo{index-1}.dat")
    record["C3_directory"] = directory
    record["C3_summary"] = summary_file

    callback("Parsing stream file...")
    start_time = time.time()
    with open(stream_file, "r", encoding="utf-8", errors="ignore") as handle:
        lines = handle.readlines()
    starts = [i for i, line in enumerate(lines) if "Begin chunk" in line]
    chunks = [lines[starts[i]: starts[i+1]] for i in range(len(starts)-1)]
    if starts:
        chunks.append(lines[starts[-1]:])

    with open(summary_file, "w", encoding="utf-8") as summary:
        for chunk in chunks:
            image_line = event_line = None
            indexed = True
            num_reflections = None
            for line_index, line in enumerate(chunk):
                if "Image filename:" in line:
                    image_line = line
                elif "Event:" in line:
                    event_line = line
                elif "indexed_by" in line and line.split()[-1] == "none":
                    indexed = False
                    break
                elif "num_reflections" in line:
                    num_reflections = int(line.split()[-1])
                elif "Reflections measured after indexing" in line:
                    if not indexed or image_line is None or event_line is None or num_reflections is None:
                        break
                    rows = chunk[line_index + 2: line_index + 2 + num_reflections]
                    parsed = np.empty((num_reflections, 4), dtype=float)
                    valid = True
                    for row_index, row in enumerate(rows):
                        fields = row.split()
                        try:
                            h, k, l = map(int, fields[:3])
                            parsed[row_index, :3] = table[h, k, l, :]
                            parsed[row_index, 3] = float(fields[3])
                        except (ValueError, IndexError):
                            valid = False
                            break
                    if not valid:
                        break
                    run_id = int(image_line.split("/")[-1].split(".")[0].split("-")[-1])
                    event_text = event_line.split(":")[-1].splitlines()[0]
                    event_id = int(event_text[5:-2])
                    print(f"{run_id:10d} {event_id:10d} {num_reflections:10d}", file=summary)
                    snapshot_path = os.path.join(directory, f"snapshot_{run_id}_{event_id}_hklI.dat")
                    np.savetxt(snapshot_path, parsed, fmt="%4d%5d%5d%30.2f")
                    break
    print(f"Parsing finished in {time.time()-start_time:.2f} seconds.")
