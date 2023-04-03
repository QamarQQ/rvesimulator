#                                                                       Modules
# =============================================================================
# Standard
import json
import os

import rvesimulator
from rvesimulator.additionals.hardening_law import HardeningLaw
from rvesimulator.additionals.microstructure_wrapper import (
    CircleMircoStructure,
)

from .base import SimulationBase

#                                                          Authorship & Credits
# =============================================================================
__author__ = "Jiaxiang Yi (J.Yi@tudelft.nl)"
__credits__ = ["Jiaxiang Yi"]
__status__ = "Stable"
# =============================================================================
#
# =============================================================================


class CDDMRVE(SimulationBase):
    def __init__(self) -> None:
        self.main_folder = os.getcwd()
        self.samples = None
        self.rve_geometry = None
        self.abaqus_paras = None
        self.sim_info = None
        self.folder_info = {
            "main_work_directory": os.path.join(os.getcwd(), "Data"),
            "script_path": os.path.dirname(abaqusrve.__file__),
            "current_work_directory": "point_1",
            "sim_path": "scriptbase.cddm_rve_script",
            "sim_script": "CDDMRVE",
            "post_path": "scriptbase.basic_script.postprocess",
            "post_script": "RVEPostProcess2D",
        }
        self.vol_req = None
        self.update_sim_info(yield_stress=0.5, a=0.2, b=0.4)

    def update_sim_info(
        self,
        size: float = 0.048,
        radius_mu: float = 0.003,
        radius_std: float = 0.000,
        vol_req: float = 0.30,
        mesh_partition: int = 100,
        strain: list = [0.05, 0.0, 0.0],
        strain_amplitude: list = None,
        simulation_time: float = 1.0,
        num_steps: int = 100,
        E_matrix: float = 100.0,
        Pr_matrix: float = 0.3,
        E_fiber: float = 1.0,
        Pr_fiber: float = 0.19,
        hardening_law: str = "swift",
        num_cpu: int = 1,
        platform: str = "ubuntu",
        seed: any = None,
        print_info: bool = False,
        **kwargs,
    ) -> None:

        self.vol_req = vol_req
        # generate the microstructure
        mircostructure_generator = CircleMircoStructure()
        microstructure_info, vol_frac = mircostructure_generator(
            size=size,
            radius_mu=radius_mu,
            radius_std=radius_std,
            vol_req=vol_req,
            seed=seed,
        )

        # generate the hardening law
        hardening = HardeningLaw()
        law_function = getattr(hardening, hardening_law)
        hardenning_table = law_function(**kwargs)

        self.sim_paras = {
            "length": size,
            "width": size,
            "radius_mu": radius_mu,
            "radius_std": radius_std,
            "vol_req": vol_req,
            "vol_frac": vol_frac,
            "mesh_partition": mesh_partition,
            "strain": strain,
            "strain_amplitude": strain_amplitude,
            "simulation_time": simulation_time,
            "num_steps": num_steps,
            "num_cpu": num_cpu,
            "platform": platform,
            "hardening_law": hardening_law,
            "hardening paras": kwargs,
            "E_matrix": E_matrix,
            "Pr_matrix": Pr_matrix,
            "E_fiber": E_fiber,
            "Pr_fiber": Pr_fiber,
        }

        if print_info is True:
            print("Simulation information: \n")
            print(json.dumps(self.sim_paras, indent=4))

        self.sim_info = {
            "job_name": "cddm_rve",
            "location_information": microstructure_info[
                "location_information"
            ],
            "radius_mu": microstructure_info["radius_mu"],
            "radius_std": microstructure_info["radius_std"],
            "len_start": microstructure_info["len_start"],
            "len_end": microstructure_info["len_end"],
            "wid_start": microstructure_info["wid_start"],
            "wid_end": microstructure_info["wid_end"],
            "mesh_partition": mesh_partition,
            "E_matrix": E_matrix,
            "Pr_matrix": Pr_matrix,
            "E_fiber": E_fiber,
            "Pr_fiber": Pr_fiber,
            "hardening_table": hardenning_table,
            "strain": strain,
            "strain_amplitude": strain_amplitude,
            "num_cpu": num_cpu,
            "platform": platform,
            "simulation_time": simulation_time,
            "num_steps": num_steps,
        }
