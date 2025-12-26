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

        while True:
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                time.sleep(0.5) 
                print("  > Result received from HFSS.")
                return True
            time.sleep(1)

    def LHSsampler(self, dims, nums, lower_bounds, upper_bounds):
        sampler = LatinHypercube(d=dims,)
        samples_continuous = sampler.random(n = nums)
        X_initial = scale(samples_continuous, lower_bounds, upper_bounds)
        return X_initial
    
    def LHSsampler(self, dims, nums, lower_bounds, upper_bounds, known_points=None):
        
        # --- 1. Handle Known Points ---
        X_known = np.empty((0, dims)) # Initialize as empty array
        n_needed = nums # Number of points left to generate via LHS

        if known_points is not None:
            X_known = np.array(known_points)
            
            # Ensure 2D shape (n_samples, n_params)
            if X_known.ndim == 1: 
                X_known = X_known.reshape(1, -1)
            
            n_known = len(X_known)
            
            # Calculate how many random LHS points are needed to fill the quota
            n_needed = max(0, nums - n_known)
            
            print(f" > Using {n_known} known points. Generating {n_needed} LHS points.")

        # --- 2. Generate Remaining Points with LHS ---
        if n_needed > 0:
            sampler = LatinHypercube(d=dims,) 
            samples_continuous = sampler.random(n=n_needed)
            X_lhs = scale(samples_continuous, lower_bounds, upper_bounds)
        else:
            # If known_points filled the quota, no LHS needed
            X_lhs = np.empty((0, dims))

        # --- 3. Combine Known and LHS Points ---
        if len(X_known) > 0:
            if len(X_lhs) > 0:
                # Stack them vertically
                X_initial = np.vstack([X_known, X_lhs])
            else:
                # If we have enough known points, just take the first 'nums' points
                X_initial = X_known[:nums] 
        else:
            # Only LHS points
            X_initial = X_lhs

        return X_initial

    def _genOutputDataFrame(self, df_current: pd.DataFrame,):
        df_output = df_current.copy()
        df_output["best"] = df_output["S11"].cummin()
        return df_output
    
    def printn(self, msg: str) -> None:
        print("\n" + "=" * 50)
        print(msg)
        print("=" * 50)




