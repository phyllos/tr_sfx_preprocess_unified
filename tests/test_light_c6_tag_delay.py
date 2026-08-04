from __future__ import annotations

import zipfile
from pathlib import Path

import h5py
import numpy as np
from openpyxl import Workbook

from functions.light.C6_pack_phyto_allInfo_light import _load_delay_file, pack_phyto_allInfo_light


def _write_tag_delay_xlsx(path: Path) -> None:
    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet("in")
    # Match the supplied workbook: one CSV-formatted string in column A per row.
    worksheet.append(["tag_number,delay,power"])
    worksheet.append(["10,1.5,101.0"])
    worksheet.append(["20,2.5,102.0"])
    worksheet.append(["30,3.5,103.0"])
    workbook.save(path)


def test_load_supplied_style_xlsx_and_zip(tmp_path: Path) -> None:
    xlsx = tmp_path / "tag_delay_all.xlsx"
    _write_tag_delay_xlsx(xlsx)

    delays, tags = _load_delay_file(xlsx, "upto1ps", "in")
    np.testing.assert_array_equal(tags, [10, 20, 30])
    np.testing.assert_allclose(delays, [1.5, 2.5, 3.5])

    archive = tmp_path / "tag_delay_all.xlsx.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.write(xlsx, arcname="tag_delay_all.xlsx")
        output.writestr("__MACOSX/._tag_delay_all.xlsx", "metadata")

    zipped_delays, zipped_tags = _load_delay_file(archive, "upto1ps", "in")
    np.testing.assert_array_equal(zipped_tags, tags)
    np.testing.assert_allclose(zipped_delays, delays)


def test_c6_joins_stream_params_and_delay_by_keys(tmp_path: Path) -> None:
    stream_h5 = tmp_path / "stream.hdf5"
    params_h5 = tmp_path / "params.hdf5"
    tag_delay = tmp_path / "tag_delay_all.xlsx"
    _write_tag_delay_xlsx(tag_delay)

    # Stream order is intentionally different from params order.
    with h5py.File(stream_h5, "w") as h5:
        h5["nRun"] = np.asarray([100, 100, 101], dtype=np.int64)
        h5["nEvent"] = np.asarray([20, 10, 30], dtype=np.int64)
        h5["nRefl"] = np.asarray([200, 100, 300], dtype=np.int64)
        h5["DRL"] = np.asarray([2.0, 1.0, 3.0])

    with h5py.File(params_h5, "w") as h5:
        h5["nRun"] = np.asarray([101, 100, 100, 102], dtype=np.int64)
        h5["nEvent"] = np.asarray([30, 10, 20, 40], dtype=np.int64)
        h5["OSF"] = np.asarray([0.3, 0.1, 0.2, 0.4])
        h5["relB"] = np.asarray([3.0, 1.0, 2.0, 4.0])

    output = pack_phyto_allInfo_light(
        stream_h5,
        params_h5,
        tag_delay,
        "upto1ps",
        tmp_path,
        "in",
    )

    with h5py.File(output, "r") as h5:
        np.testing.assert_array_equal(h5["runID"][()], [100, 100, 101])
        np.testing.assert_array_equal(h5["eventID"][()], [20, 10, 30])
        np.testing.assert_allclose(h5["delay"][()], [2.5, 1.5, 3.5])
        np.testing.assert_allclose(h5["OSF"][()], [0.2, 0.1, 0.3])
        np.testing.assert_allclose(h5["relB"][()], [2.0, 1.0, 3.0])
        assert h5.attrs["matched_snapshots"] == 3
        assert h5.attrs["missing_params_snapshots"] == 0
        assert h5.attrs["missing_delay_snapshots"] == 0
