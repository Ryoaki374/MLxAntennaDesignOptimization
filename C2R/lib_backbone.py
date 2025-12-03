# Import AppConfig from lib_config.py
from lib_config import AppConfig
from datetime import datetime
from scipy.stats.qmc import LatinHypercube, scale
import h5py
import os
import time
import json
import pandas as pd
import numpy as np

class Backbone:

    def __init__(self, config: AppConfig,):
        self.cfg = config
        self.h5f = None
        self.current_sim_id = 0 

    def mkdir(self):
        if not hasattr(self, "dir_run"): # attribute check
            timestamp = datetime.now().strftime("%m%d%H%M%S")
            self.dir_run = self.cfg.env.dir_base / f"{timestamp}"
            self.dir_run.mkdir(exist_ok=True)
            print(f"Created new run directory: {self.dir_run}")

    def _get_dir_run(self):
        return self.dir_run
    
    def initStorer(self, runs_dir = None, mode = "w"):
        """Initializes settings for saving data to an HDF5 file."""
        
        self.mkdir()

        if runs_dir is None:
            runs_dir = self.dir_run

        filepath = runs_dir / "results.h5"

        self.h5f = h5py.File(filepath, mode)
        grp_input = self.h5f.create_group("input")
        grp_output = self.h5f.create_group("output")
        grp_lc = self.h5f.create_group("learning_curve")
        print(f"HDF5 dataset created at: {filepath}")

    def _addNewDatasetToHDF(self, df: pd.DataFrame, grp_name_str: str, dset_name_str: str):
        
        grp = self.h5f[grp_name_str]

        if dset_name_str in grp:
            return grp[dset_name_str]
        
        data = df.to_numpy(dtype=np.float32) # without header
        n_rows, n_cols = data.shape

        dset = grp.create_dataset(
            dset_name_str,
            shape=(n_rows, n_cols),
            dtype=np.float32,
            compression="gzip",
        )

        # column name
        dset.attrs["columns"] = json.dumps(df.columns.tolist())

        # write data
        dset[:, :] = data

        print(f"wrote {n_rows} rows x {n_cols} cols to {dset_name_str}")

    def _getSimulationID(self):
        self.current_sim_id += 1
        return self.current_sim_id

    
    def call_subroutine(self, config, index, param_names, param_values, unit="mm", value_fmt="{:.2f}"):
        input_file = config["INPUT_FILE"]
        results_file = config["RESULTS_FILE"]
        temp_file = config["TEMP_FILE"]

        row = {'*': index}
        for k, v in zip(param_names, param_values):
            row[k] = f"{value_fmt.format(float(v))}{unit}" if unit else value_fmt.format(float(v))

        pd.DataFrame([row]).to_csv(input_file, index=False)

        print("  > Waiting for HFSS simulation to complete...")
        # lines_before = 0

        # if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
        #     print("  > Result received from HFSS.")
        #     return True
        
        #start_time = time.time()
        # timeout = 1000
        while True:
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                time.sleep(0.5) 
                print("  > Result received from HFSS.")
                return True
            time.sleep(1)
        
        #print(f"  > [Error] Simulation timed out after {timeout} seconds.")
        #return False

        #while True:
        #    lines_after = 0
        #    if os.path.exists(results_file) and os.path.getsize(results_file) > 0:
        #        with open(results_file, 'r') as f:
        #            lines_after = len(f.readlines())

        #    if lines_after > lines_before:
        #        print("  > Result received from HFSS.")
        #        time.sleep(0.5)
        #        return True

        #    time.sleep(1)

    def LHSsampler(self, dims, lower_bounds, upper_bounds):
        sampler = LatinHypercube(d=dims)
        samples_continuous = sampler.random(n = self.cfg.sim.n_init)
        #X_initial = scale(samples_continuous, self.cfg.sim.lower_bounds[:], self.cfg.sim.upper_bounds[:])
        X_initial = scale(samples_continuous, lower_bounds, upper_bounds)
        return X_initial
    
    def _genOutputDataFrame(self, df_current: pd.DataFrame, acq_values: np.ndarray):
        df_output = df_current.copy()
        # df_output = df_output.rename(columns={"*": "epoch"})
        df_output["best"] = df_output["S11"].cummin()
        full_acq_col = np.full(len(df_output), np.nan)
        full_acq_col[self.cfg.sim.n_init:] = acq_values
        df_output["acq"] = full_acq_col
        return df_output
    
    def printn(self, msg: str) -> None:
        print("\n" + "=" * 50)
        print(msg)
        print("=" * 50)




