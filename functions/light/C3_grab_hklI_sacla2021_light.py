import os
import re
import argparse
import numpy as np


def symP212121(hkl):
    h, k, l = [int(x) for x in hkl]
    if h >= 0 and k >= 0 and l >= 0:
        return h, k, l
    if h >= 0 and k <= 0 and l <= 0:
        return h, -k, -l
    if h <= 0 and k >= 0 and l <= 0:
        return -h, k, -l
    if h <= 0 and k <= 0 and l >= 0:
        return -h, -k, l
    if h <= 0 and k >= 0 and l >= 0:
        return -h, k, l
    if h >= 0 and k <= 0 and l >= 0:
        return h, -k, l
    if h >= 0 and k >= 0 and l <= 0:
        return h, k, -l
    if h < 0 and k < 0 and l < 0:
        return -h, -k, -l
    return h, k, l


def _chunks(lines):
    chunk = []
    in_chunk = False
    for line in lines:
        if 'Begin chunk' in line:
            chunk = [line]
            in_chunk = True
        elif 'End chunk' in line and in_chunk:
            chunk.append(line)
            yield chunk
            chunk = []
            in_chunk = False
        elif in_chunk:
            chunk.append(line)


def _reflection_rows(chunk):
    rows = []
    in_block = False
    for line in chunk:
        if line.startswith('Reflections measured after indexing'):
            in_block = True
            continue
        if in_block and line.startswith('End of reflections'):
            break
        if not in_block:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            h, k, l = int(parts[0]), int(parts[1]), int(parts[2])
            I = float(parts[3])
        except ValueError:
            continue
        hh, kk, ll = symP212121((h, k, l))
        rows.append((hh, kk, ll, I))
    return rows


def grab_hklI_sacla2021_light(stream_file, data_name, folder_path='.'):
    """Extract one hklI DAT file per indexed snapshot from a SACLA stream."""
    stream_file = os.path.abspath(stream_file)
    out_dir = os.path.join(folder_path, f'sacla2021_{data_name}_hklI')
    os.makedirs(out_dir, exist_ok=True)
    summary = os.path.join(folder_path, f'{data_name}_snapshotInfo.dat')

    with open(stream_file, 'r', errors='ignore') as f:
        lines = f.readlines()

    n_saved = 0
    with open(summary, 'w') as fs:
        for ch in _chunks(lines):
            text = ''.join(ch)
            m_index = re.search(r'indexed_by\s*=\s*(\S+)', text)
            if m_index and m_index.group(1).lower() == 'none':
                continue
            m_run = re.search(r'run(\d+)', text)
            m_tag = re.search(r'tag-?(\d+)', text)
            m_refl = re.search(r'num_reflections\s*=\s*(\d+)', text)
            if not (m_run and m_tag and m_refl):
                continue
            runID = int(m_run.group(1))
            eventID = int(m_tag.group(1))
            rows = _reflection_rows(ch)
            if not rows:
                continue
            n_saved += 1
            fs.write(f'{runID:10d} {eventID:16d} {len(rows):10d}\n')
            out_file = os.path.join(out_dir, f'sacla2021_run{runID}_tag{eventID}_hklI.dat')
            np.savetxt(out_file, np.asarray(rows), fmt='%4d %5d %5d %11.2f')
    print(f'Saved {n_saved} hklI files in {out_dir}')
    print(f'Saved {summary}')
    return out_dir


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('stream_file')
    p.add_argument('--data-name', required=True)
    p.add_argument('--folder', default='.')
    args = p.parse_args()
    grab_hklI_sacla2021_light(args.stream_file, args.data_name, args.folder)
