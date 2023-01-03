# import system packages
import json
import os
import pickle

import numpy as np
import pandas

# local functions
import rvesimulator
from rvesimulator.simulators.abaqus_simulator import AbaqusSimulator
from rvesimulator.simulators.utils import create_dir


class SimulatorCaller:
    def __init__(self) -> None:

        """Interface between python and abaqus of the asca rve case"""
        self.main_folder = os.getcwd()
        self.samples = None
        self.rve_geometry = None
        self.abaqus_paras = None
        self.sim_info = None
        self.folder_info = {
            "main_work_directory": os.path.join(os.getcwd(), "Data"),
            "script_path": os.path.dirname(rvesimulator.__file__),
            "current_work_directory": "point_1",
            "sim_path": "scriptbase.pnas_rve",
            "sim_script": "PnasHollowPlate",
            "post_path": "scriptbase.postprocess",
            "post_script": "RVEPostProcess",
        }
        self.vol_req = None
        self.update_sim_info(print_info=True)

    def run_simulation(
        self, data: dict = None, save_source_files: bool = True
    ) -> dict:
        """run simulation sequentially

        Parameters
        ----------
        data : dict, optional
            design of experiments without responses
        save_source_files: bool, optional
            if True, it will create a new folder for every sample and
            more memory is needed for the simulation task
            other wise the simulation will be excuted in the Data/data
            folder and the simulation result will be save as Data/data.pickle
            file.

        Returns
        -------
        pandas.DataFrame
            design of experiments with responses
        """
        # number of samples
        self.data = data
        samples = data["samples"].to_dict("records")
        responses = data["responses"]
        num_samples = len(samples)
        for ii in range(num_samples):
            # update the simulation information
            if save_source_files is True:
                self.folder_info["current_work_directory"] = "point_" + str(ii)
                new_path = create_dir(
                    current_folder=self.folder_info["main_work_directory"],
                    dirname=self.folder_info["current_work_directory"],
                )
                os.chdir(new_path)
            else:
                self.folder_info["current_work_directory"] = "data"
                new_path = create_dir(
                    current_folder=self.folder_info["main_work_directory"],
                    dirname=self.folder_info["current_work_directory"],
                )
                os.chdir(new_path)

            # update the geometry info for microstructure
            self._update_sample_info(sample=samples[ii])
            os.chdir(self.main_folder)
            # initilize the abaqus simulator
            abaqus_wrapper = AbaqusSimulator(
                sim_info=self.sim_info, folder_info=self.folder_info
            )
            abaqus_wrapper.run()
            results = abaqus_wrapper.read_back_results()
            # update DoE information
            for jj in range(len(list(responses.keys()))):
                responses.at[ii, list(responses.keys())[jj]] = results[
                    list(responses.keys())[jj]
                ]

            self._save_data(responses)

        return self.data

    def update_sim_info(
        self,
        size: float = 1.0,
        radius: float = 0.2,
        youngs_modulus: float = 100.0,
        poission_ratio: int = 0.3,
        mesh_partition: int = 100,
        yield_table: str = "Von_mises",
        loads: list = [0.02, 0.02, 0.02],
        loads_path: list = None,
        time_period: float = 1.0,
        print_info: bool = False,
    ) -> None:
        """update the simulation information, if the input is None then
        use the default value.

        Parameters
        ----------
        size : float, optional
            size of RVE, by default 1.0
        radius : float, optional
            radius of hollow plate , by default 0.2
        youngs_modulus : float, optional
            young's modulus, by default 100.0
        poission_ratio : int, optional
            poission ratio, by default 0.3
        mesh_partition : int, optional
            mesh portion, by default 100
        yield_table : list, optional
            yield criterion, by default None
        loads : list, optional
            maximum loads, by default [0.02, 0.02, 0.02]
        loads_path : list, optional
            loads path, by default None
        time_period : float, optional
            simulation time , by default 1.0
        print_info : bool, optional
            print the default information or not, by default False
        """
        if yield_table == "Von_mises":
            yield_criterion = np.zeros((101, 2))
            yield_criterion[:, 1] = np.linspace(0, 1, 101)
            yield_criterion[:, 0] = 0.5 + 0.2 * (yield_criterion[:, 1]) ** 0.4
            yield_criterion[-1, 1] = 10.0
            yield_criterion[-1, 0] = (
                0.5 + 0.2 * (yield_criterion[-1, 1]) ** 0.4
            )
            yield_criterion = yield_criterion.T
        else:
            raise KeyError("The material's yield criterion is not defined! \n")

        self.sim_info = {
            "length": size,
            "width": size,
            "radius": radius,
            "youngs_modulus": youngs_modulus,
            "poission_ratio": poission_ratio,
            "yield_table": yield_criterion.tolist(),
            "mesh_partition": mesh_partition,
            "loads": loads,
            "loads_path": loads_path,
            "time_period": time_period,
            "job_name": "pnas_hollow_plate",
        }
        if print_info is True:
            print(f"The simulation information is : {self.sim_info}")

    def _update_sample_info(self, sample) -> None:
        """update the design variables"""
        self.sim_info.update(sample)

    def _save_data(self, responses) -> None:
        """save data to json file"""
        self.data["responses"] = responses
        working_folder = os.getcwd()
        with open("data.pickle", "wb") as file:
            pickle.dump(self.data, file)
        os.chdir(working_folder)
