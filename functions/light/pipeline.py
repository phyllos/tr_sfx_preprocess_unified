from __future__ import annotations

import sys
from pathlib import Path

MODE_DIR = Path(__file__).resolve().parent
if str(MODE_DIR) not in sys.path:
    sys.path.insert(0, str(MODE_DIR))

from C1_read_partialator_params_light import read_partialator_params_light
from C2_read_stream_files_light import read_stream_files_light
from C3_grab_hklI_sacla2021_light import grab_hklI_sacla2021_light
from C4_find_hkl_max_light import find_hkl_max_light
from C5_find_hkl_redundancy_light import find_hkl_redundancy_light
from C6_pack_phyto_allInfo_light import pack_phyto_allInfo_light
from C7_pack_phyto_final_light import pack_phyto_final_light
from C8_generate_uniform_delay_sacla2021_hdf5 import generate_uniform_delay_sacla2021_hdf5
from C9_pack_phyto_light_lpf import pack_phyto_light_lpf
from C10_generate_maskDRL_light import generate_maskDRL_light
from C11_pack_phyto_light_lpf_drl import pack_phyto_light_lpf_drl
from C12_pack_phyto_light_lpf_drl_scl import pack_phyto_light_lpf_drl_scl
from C13_pack_phyto_light_lpf_drl_scl_bst import pack_phyto_light_lpf_drl_scl_bst


def stage_file(state, suffix):
    cfg = state["config"]
    return str(cfg["output"]["directory"] / f"dataPhyto_{cfg['dataset']['name']}_{suffix}.hdf5")


def c1(state):
    cfg=state["config"]; path=read_partialator_params_light(str(cfg["inputs"]["params"]), str(cfg["output"]["directory"]), cfg["dataset"]["name"]); state["artifacts"]["C1_file"]=str(path)
def c2(state):
    cfg=state["config"]; path=read_stream_files_light(str(cfg["inputs"]["stream"]), cfg["dataset"]["name"], str(cfg["output"]["directory"])); state["artifacts"]["C2_file"]=str(path)
def c3(state):
    cfg=state["config"]; path=grab_hklI_sacla2021_light(str(cfg["inputs"]["stream"]), cfg["dataset"]["name"], str(cfg["output"]["directory"])); state["artifacts"]["C3_hklI_folder"]=str(path)
def c4(state):
    cfg=state["config"]; path=find_hkl_max_light(state["artifacts"]["C3_hklI_folder"], cfg["dataset"]["name"], str(cfg["output"]["directory"])); state["artifacts"]["C4_file"]=str(path)
def c5(state):
    cfg=state["config"]; path=find_hkl_redundancy_light(state["artifacts"]["C3_hklI_folder"], state["artifacts"]["C4_file"], cfg["dataset"]["name"], str(cfg["output"]["directory"])); state["artifacts"]["C5_file"]=str(path)
def c6(state):
    cfg = state["config"]
    inputs = cfg["inputs"]
    tag_delay_file = inputs.get("tag_delay_file") or inputs.get("delays")
    if tag_delay_file is None:
        raise KeyError("Light C6 requires inputs.tag_delay_file (or legacy inputs.delays).")
    delay_cfg = cfg.get("delay_input", {})
    path = pack_phyto_allInfo_light(
        state["artifacts"]["C2_file"],
        state["artifacts"]["C1_file"],
        str(tag_delay_file),
        cfg["dataset"]["name"],
        str(cfg["output"]["directory"]),
        delay_cfg.get("sheet"),
    )
    state["artifacts"]["C6_file"] = str(path)
def c7(state):
    cfg=state["config"]; dat=str(Path(state["artifacts"]["C6_file"]).with_suffix(".dat")); path=pack_phyto_final_light(dat, state["artifacts"]["C5_file"], state["artifacts"]["C3_hklI_folder"], cfg["dataset"]["name"], str(cfg["output"]["directory"]), bool(cfg.get("processing",{}).get("remove_negative_pixels",False))); state["artifacts"]["C7_file"]=str(path)
def c8(state):
    cfg=state["config"]; select=cfg.get("selection",{}); source=state["artifacts"].get("C7_file") or str(cfg["inputs"]["c7_file"]); path=generate_uniform_delay_sacla2021_hdf5(source, stage_file(state,"C8_unifdelay"), int(select.get("samples_per_delay",155)), float(select.get("tmin",-84)), float(select.get("tmax",550)), select.get("random_seed")); state["artifacts"]["C8_file"]=str(path)
def c9(state):
    cfg=state["config"]; crystal=cfg.get("crystal",{}); path=pack_phyto_light_lpf(state["artifacts"]["C8_file"], stage_file(state,"C9_LPF"), float(crystal.get("a",54.22)), float(crystal.get("b",115.78)), float(crystal.get("c",117.08)), float(crystal.get("wavelength",1.77))); state["artifacts"]["C9_file"]=str(path)
def c10(state):
    cfg=state["config"]; proc=cfg.get("processing",{}); crystal=cfg.get("crystal",{}); 
    if proc.get("make_drl_mask",False) or proc.get("use_drl_mask",False):
        path=generate_maskDRL_light(state["artifacts"]["C9_file"], str(cfg["output"]["directory"] / f"maskDRL_{cfg['dataset']['name']}.hdf5"), float(crystal.get("a",54.22)), float(crystal.get("b",115.78)), float(crystal.get("c",117.08))); state["artifacts"]["C10_mask_file"]=str(path)
def c11(state):
    cfg=state["config"]; proc=cfg.get("processing",{}); mask=state["artifacts"].get("C10_mask_file") if proc.get("use_drl_mask",False) else None; path=pack_phyto_light_lpf_drl(state["artifacts"]["C9_file"], stage_file(state,"C11_LPF_DRL"), mask); state["artifacts"]["C11_file"]=str(path)
def c12(state):
    cfg=state["config"]; crystal=cfg.get("crystal",{}); path=pack_phyto_light_lpf_drl_scl(state["artifacts"]["C11_file"], stage_file(state,"C12_LPF_DRL_SCL"), float(crystal.get("a",54.22)), float(crystal.get("b",115.78)), float(crystal.get("c",117.08)), bool(cfg.get("processing",{}).get("generate_hkl_average",True))); state["artifacts"]["C12_file"]=str(path)
def c13(state):
    path=pack_phyto_light_lpf_drl_scl_bst(state["artifacts"]["C12_file"], stage_file(state,"C13_LPF_DRL_SCL_BST")); state["artifacts"]["C13_file"]=str(path)


def prepare_state(state):
    inputs=state["config"]["inputs"]
    if "c7_file" in inputs:
        state["artifacts"].setdefault("C7_file", str(inputs["c7_file"]))


def get_pipeline():
    return [("C1",c1),("C2",c2),("C3",c3),("C4",c4),("C5",c5),("C6",c6),("C7",c7),("C8",c8),("C9",c9),("C10",c10),("C11",c11),("C12",c12),("C13",c13)]
