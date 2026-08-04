from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]


def _run(config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "driver.py"), "--config", str(config)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def _write_light_sparse(h5: h5py.File, name: str, matrix) -> None:
    matrix = sparse.csc_matrix(matrix)
    group = h5.create_group(name)
    group.attrs["format"] = "csc"
    group.create_dataset("data", data=matrix.data)
    group.create_dataset("indices", data=matrix.indices.astype(np.int64))
    group.create_dataset("indptr", data=matrix.indptr.astype(np.int64))
    group.create_dataset("shape", data=np.asarray(matrix.shape, dtype=np.int64))


def _write_dark_sparse(h5: h5py.File, name: str, matrix) -> None:
    matrix = sparse.csr_matrix(matrix)
    group = h5.create_group(f"{name}_csr")
    group.attrs["shape"] = matrix.shape
    group.create_dataset("data", data=matrix.data)
    group.create_dataset("indices", data=matrix.indices)
    group.create_dataset("indptr", data=matrix.indptr)


def _example_matrices():
    intensity = np.asarray(
        [
            [10.0, 0.0, 3.0],
            [12.0, 2.0, 0.0],
            [9.0, 1.0, 4.0],
            [11.0, 0.0, 5.0],
        ]
    )
    mask = (intensity != 0.0).astype(float)
    return intensity, mask


def test_light_c8_to_c13_smoke(tmp_path: Path) -> None:
    intensity, mask = _example_matrices()
    source = tmp_path / "light_c7.hdf5"
    output = tmp_path / "light_output"

    with h5py.File(source, "w") as h5:
        _write_light_sparse(h5, "T", intensity)
        _write_light_sparse(h5, "M", mask)
        h5["delay"] = np.asarray([-1.0, 0.0, 0.0, 1.0])
        h5["DRL"] = np.ones(4)
        h5["runID"] = np.ones(4, dtype=np.int64)
        h5["eventID"] = np.asarray([10, 11, 12, 13])
        h5["OSF"] = np.asarray([0.1, 0.2, 0.3, 0.4])
        h5["relB"] = np.asarray([0.01, 0.02, 0.03, 0.04])
        h5["miller_h"] = np.asarray([1, 2, 3])
        h5["miller_k"] = np.asarray([0, 1, 1])
        h5["miller_l"] = np.asarray([1, 1, 2])
        h5["sort_notice"] = np.bytes_("smoke")
        h5["notice_negative_pix"] = np.bytes_("smoke")

    config = tmp_path / "light.yaml"
    config.write_text(
        f"""
dataset:
  mode: light
  name: smoke
inputs:
  c7_file: {source}
output:
  directory: {output}
pipeline:
  start_step: C8
  stop_step: C13
crystal:
  a: 54.22
  b: 115.78
  c: 117.08
  wavelength: 1.77
selection:
  samples_per_delay: 2
  tmin: -2
  tmax: 2
  random_seed: 42
processing:
  make_drl_mask: false
  use_drl_mask: false
  generate_hkl_average: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run(config)
    assert "Pipeline complete" in result.stdout
    assert (output / "dataPhyto_smoke_C13_LPF_DRL_SCL_BST.hdf5").is_file()
    assert (output / "dataPhyto_smoke_C12_LPF_DRL_SCL_AVG.hkl").is_file()


def test_dark_c8_to_c9_smoke(tmp_path: Path) -> None:
    intensity, mask = _example_matrices()
    packed_dir = tmp_path / "dark_packed"
    packed_dir.mkdir()
    c7_file = packed_dir / "c7.hdf5"
    c6_file = tmp_path / "c6.hdf5"

    with h5py.File(c7_file, "w") as h5:
        _write_dark_sparse(h5, "T", intensity)
        _write_dark_sparse(h5, "M", mask)
        h5["miller_h"] = np.asarray([1, 2, 3])
        h5["miller_k"] = np.asarray([0, 1, 1])
        h5["miller_l"] = np.asarray([1, 1, 2])
        h5["sort_notice"] = np.bytes_("smoke")
        h5["notice_negative_pix"] = np.bytes_("smoke")

    with h5py.File(c6_file, "w") as h5:
        h5["OSF"] = np.asarray([1.1, 1.2, 1.3, 1.4])
        h5["relB"] = np.asarray([0.01, 0.02, 0.03, 0.04])

    config = tmp_path / "dark.yaml"
    config.write_text(
        f"""
dataset:
  mode: dark
  name: smoke
inputs:
  c6_file: {c6_file}
  c7_file: {c7_file}
  c7_directory: {packed_dir}
output:
  directory: {tmp_path / 'unused_output'}
pipeline:
  start_step: C8
  stop_step: C9
crystal:
  a: 78.1
  b: 78.1
  c: 38.4
processing:
  data_type: Intensity
  remove_negative_pixels: false
  generate_hkl_average: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = _run(config)
    assert "Pipeline complete" in result.stdout
    assert (packed_dir / "data_dark_int_sortEvent_scl_bst_nS4_nBrg3.hdf5").is_file()
    assert (packed_dir / "data_dark_int_sortEvent_scl_avg_nS4_nBrg3.hkl").is_file()
