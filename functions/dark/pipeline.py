from __future__ import annotations

import sys
from pathlib import Path

MODE_DIR = Path(__file__).resolve().parent
if str(MODE_DIR) not in sys.path:
    sys.path.insert(0, str(MODE_DIR))

from C1_read_partialator_params import read_partialator_params
from C2_read_stream_files import read_stream_files
from C3_grab_DARK_pyxtal_wyckoffs import grab_DARK
from C4_find_hkl_max import find_hkl_max
from C5_find_hkl_redundancy import find_hkl_redundancy
from C6_pack_allInfo_dark import pack_allInfo_dark
from C7_pack_final_dark import pack_final_dark
from C8_script_pack_dark_scl import pack_dark_scl
from C9_script_pack_phyto_dark_bst import pack_phyto_dark_bst


def progress(message): print(f"[progress] {message}", flush=True)

def c1(state):
    cfg=state["config"]; read_partialator_params(progress, str(cfg["inputs"]["params"]), str(cfg["output"]["directory"]), state["artifacts"])
def c2(state):
    cfg=state["config"]; read_stream_files(str(cfg["inputs"]["stream"]), cfg["dataset"]["name"], str(cfg["output"]["directory"]), Path(state["artifacts"]["C1_directory"]).name, state["artifacts"])
def c3(state):
    cfg=state["config"]; adv=cfg.get("advanced",{}); grab_DARK(progress, state["artifacts"], str(cfg["output"]["directory"]), str(cfg["inputs"]["stream"]), int(cfg.get("crystal",{}).get("space_group",19)), int(adv.get("h_max",100)), int(adv.get("k_max",100)), int(adv.get("l_max",100)))
def c4(state):
    cfg=state["config"]; find_hkl_max(progress, state["artifacts"]["C3_directory"], state["artifacts"]["C3_summary"], "snapshot", str(cfg["output"]["directory"]), state["artifacts"])
def c5(state):
    cfg=state["config"]; find_hkl_redundancy(progress, state["artifacts"]["C3_directory"], state["artifacts"]["C3_summary"], "snapshot", str(cfg["output"]["directory"]), state["artifacts"]["C4_file"], state["artifacts"])
def c6(state):
    cfg=state["config"]; pack_allInfo_dark(progress, state["artifacts"]["C1_file"], state["artifacts"]["C2_file"], state["artifacts"]["C3_summary"], str(cfg["output"]["directory"]), state["artifacts"])
def c7(state):
    cfg=state["config"]; proc=cfg.get("processing",{}); pack_final_dark(progress, str(cfg["inputs"]["stream"]), state["artifacts"], str(cfg["output"]["directory"]), state["artifacts"]["C3_directory"], state["artifacts"]["C3_summary"], "snapshot", state["artifacts"]["C4_file"], state["artifacts"]["C5_file"], "dark", proc.get("data_type","Intensity"), True, bool(proc.get("remove_negative_pixels",False)))
def c8(state):
    cfg=state["config"]; crystal=cfg.get("crystal",{}); proc=cfg.get("processing",{}); pack_dark_scl(progress, state["artifacts"]["C7_directory"], state["artifacts"]["C7_file"], state["artifacts"]["C6_file"], float(crystal.get("a",78.1)), float(crystal.get("b",78.1)), float(crystal.get("c",38.4)), state["artifacts"], "dark", "amp" if str(proc.get("data_type","Intensity")).lower().startswith("amp") else "int", bool(proc.get("generate_hkl_average",True)), bool(proc.get("remove_negative_pixels",False)))
def c9(state):
    cfg=state["config"]; proc=cfg.get("processing",{}); pack_phyto_dark_bst(progress, state["artifacts"]["C8_hdf5_file"], state["artifacts"]["C7_file"], state["artifacts"], state["artifacts"]["C7_directory"], "dark", "amp" if str(proc.get("data_type","Intensity")).lower().startswith("amp") else "int")


def prepare_state(state):
    inputs=state["config"]["inputs"]
    mapping={"c6_file":"C6_file","c7_file":"C7_file","c7_directory":"C7_directory"}
    for key, artifact in mapping.items():
        if key in inputs: state["artifacts"].setdefault(artifact, str(inputs[key]))


def get_pipeline():
    return [("C1",c1),("C2",c2),("C3",c3),("C4",c4),("C5",c5),("C6",c6),("C7",c7),("C8",c8),("C9",c9)]
