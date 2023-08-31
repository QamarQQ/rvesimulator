#                                                                       Modules
# =============================================================================
# Standard
import json
import os
from typing import Any

import rvesimulator
from rvesimulator.additions.microstructure_wrapper import CircleMircoStructure

from .shared_functionalities import SimulationBase

#                                                         Authorship & Credits
# =============================================================================
__author__ = "Jiaxiang Yi (J.Yi@tudelft.nl)"
__credits__ = ["Jiaxiang Yi"]
__status__ = "Stable"
# =============================================================================

# =============================================================================


class VeniNoCohRVE(SimulationBase):
    """uni-axial tension for pp/pe composite without cohesive elements in
    between fiber and matrix material phases"""

    def __init__(self) -> None:
        """Interface between python and abaqus of the Hollow plate case"""
        self.main_folder = os.getcwd()
        self.folder_info = {
            "main_work_directory": os.path.join(self.main_folder, "Data"),
            "script_path": os.path.dirname(rvesimulator.__file__) + \
                "/scriptbase/",
            "current_work_directory": "point_1",
            "sim_path": "benchmark_abaqus_scripts.veni_nocohesive_rve",
            "sim_script": "VeniNoCohRVE",
            "post_path": "benchmark_abaqus_scripts.veni_nocohesive_rve",
            "post_script": "PostProcess",
        }
        self.subroutine_path = self.folder_info["script_path"] + \
            "benchmark_abaqus_scripts/vevp_leonov_model.f"
        self.update_sim_info()

    def update_sim_info(
        self,
        size: float = 0.02,
        radius_mu: float = 0.0031,
        radius_std: float = 0.0,
        vol_req: float = 0.30,
        paras_pp: list = [
            748.234,
            0.45,
            296.0,
            0.1,
            1.53e-02,
            6.608e-01,
            7.33e02,
            2.51e08,
            3.30e-26,
            7.42e06,
            2.67e-02,
            4.826e1,
            1.520,
            1.303,
        ],
        paras_pe: list = [
            611.6,
            0.45,
            296.0,
            0.1,
            4.40e-01,
            5.1e-03,
            772.1,
            2.29e08,
            9.94e-26,
            5.01e06,
            3.234e-01,
            15.88,
            13.52,
            0.043,
        ],
        mesh_partition: int = 100,
        strain: list = [0.1, 0.0, 0.0],
        num_steps: int = 1000,
        simulation_time: float = 100.0,
        num_cpu: int = 8,
        platform: str = "ubuntu",
        seed: Any = None,
        print_info: bool = False,
    ) -> None:
        # get the micro_structure information
        mirco_structure_generator = CircleMircoStructure()
        microstructure_info, vol_frac = mirco_structure_generator(
            size=size,
            radius_mu=radius_mu,
            radius_std=radius_std,
            vol_req=vol_req,
            seed=seed,
        )

        self.sim_paras = {
            "size": size,
            "radius_mu": radius_mu,
            "radius_std": radius_std,
            "vol_req": vol_req,
            "vol_frac": vol_frac,
            "paras_pp": paras_pp,
            "paras_pe": paras_pe,
            "mesh_partition": mesh_partition,
            "strain": strain,
            "num_steps": num_steps,
            "simulation_time": simulation_time,
            "num_cpu": num_cpu,
            "platform": platform, }

        self.sim_info = {
            "job_name": "veni_nocoh_rve",
            "location_information": microstructure_info[
                "location_information"
            ],
            "radius_mu": microstructure_info["radius_mu"],
            "radius_std": microstructure_info["radius_std"],
            "len_start": microstructure_info["len_start"],
            "len_end": microstructure_info["len_end"],
            "wid_start": microstructure_info["wid_start"],
            "wid_end": microstructure_info["wid_end"],
            "paras_pp": paras_pp,
            "paras_pe": paras_pe,
            "mesh_partition": mesh_partition,
            "num_steps": num_steps,
            "simulation_time": simulation_time,
            "strain": strain,
            "num_cpu": num_cpu,
            "platform": platform,
            "subroutine_path": self.subroutine_path
        }

        # print simulation information to screen
        if print_info:
            self._print_sim_info(info=self.sim_paras)
