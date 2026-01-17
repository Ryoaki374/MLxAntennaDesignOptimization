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
from pathlib import Path

import lib_RFdesign

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
    
    def _get_path_models(self):
        base = self.dir_run
        files = self.cfg.hfss.filename_models
        return [base / f for f in files], [str(base / f) for f in files]
        
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

    '''
    def call_subroutine(self, config, index, param_names, param_values, value_fmt="{:.2f}"):
        modelpaths = self._get_path_models()
        #input_file = config["INPUT_FILE"]
        input_file = str(self.dir_run / self.cfg.io.filename_input)
        #results_file = config["RESULTS_FILE"]
        #temp_file = config["TEMP_FILE"]
        temp_file = str(self.dir_run / self.cfg.io.filename_temp)
        #unit_arr = config["param_units"]
        unit_arr = self.cfg.hfss.param_units

        #param_names = self.cfg.hfss.param_names
        param_names_step = self.cfg.hfss.param_names[-2:]
        param_values_step = param_values[-2:]
        
        param_names = self.cfg.hfss.param_names[:4]
        param_values = param_values[:4]

        unit_arr = unit_arr[:4]

        # Create step file for Backshort
        design = lib_RFdesign.ConvexBackshort(model_path=modelpaths[0])
        a = 9.525
        b = 4.7625
        c = param_values_step[0]
        k = int(param_values_step[1])
        convex_backshort = design.genBackshort(a=a, b=b, c=c, k=k, grid_res=30, shifts=(0, -4.7625, -0.34575))
        #design.plotConvex3D(convex_backshort) 
        # 
        # Create step file for Finshape
        design = lib_RFdesign.ConvexFinshape(model_path=modelpaths[1])
        a = param_values[0]
        b = param_values[1]
        k = param_values[2]
        convex_finshape = design.genFinshape(a=a, b=b, k=k, grid_res=400, shifts=(0.0, -1.0))
        design.plotProfile2D(convex_finshape)

        row = {'*': index}
        
        for k, v, u in zip(self.cfg.hfss.param_names, param_values, unit_arr):
            formatted_val = value_fmt.format(float(v))
            row[k] = f"{formatted_val}{u}" if u else formatted_val
    
        pd.DataFrame([row]).to_csv(input_file, index=False)
    
        while True:
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                time.sleep(0.5) 
                print("  > Result received from HFSS.")
                return True
            time.sleep(1)
    '''

    def call_subroutine(self, config, index, param_names, param_values, value_fmt="{:.2f}"):
        model_paths, _ = self._get_path_models()
        #input_file = config["INPUT_FILE"]
        #input_file = str(self.dir_run / self.cfg.io.filename_input)
        #results_file = config["RESULTS_FILE"]
        #temp_file = config["TEMP_FILE"]
        temp_file = str(self.dir_run / self.cfg.io.filename_temp)
        #unit_arr = config["param_units"]
        #unit_arr = self.cfg.hfss.param_units

        #param_names = self.cfg.hfss.param_names
        #param_names_step = self.cfg.hfss.param_names[-2:]
        #param_values_step = param_values[-2:]
        
        #param_names = self.cfg.hfss.param_names[:4]
        #param_values = param_values[:4]

        #unit_arr = unit_arr[:4]

        # Create step file for Backshort
        design = lib_RFdesign.ConvexBackshort(model_path=model_paths[0])
        a = 9.525
        b = 4.7625
        c = param_values[0]
        k = int(param_values[1])
        convex_backshort = design.genBackshort(a=a, b=b, c=c, k=k, grid_res=30, shifts=(0, -4.7625, -0.34575))
        #design.plotConvex3D(convex_backshort) 
        # 
        # Create step file for Finshape
        design = lib_RFdesign.ConvexFinshape(model_path=model_paths[1])
        a = param_values[2]
        b = param_values[3]
        k = param_values[4]
        print(param_values)
        convex_finshape = design.genFinshape(a=a, b=b, k=k, grid_res=400, shifts=(0.0, -1.0))
        #design.plotProfile2D(convex_finshape)

        #row = {'*': index}
        #
        #for k, v, u in zip(self.cfg.hfss.param_names, param_values, unit_arr):
        #    formatted_val = value_fmt.format(float(v))
        #    row[k] = f"{formatted_val}{u}" if u else formatted_val
    
        #pd.DataFrame([row]).to_csv(input_file, index=False) should be detelted
    
        while True:
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                time.sleep(0.5) 
                print("  > Result received from HFSS.")
                return True
            time.sleep(1)

    def LHSsampler(self, dims, nums, lower_bounds, upper_bounds):
        sampler = LatinHypercube(d = dims,)
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
    
    def in_bounds(self, x, lb, ub):
        return all(l <= v <= u for v, l, u in zip(x, lb, ub))

    def all_in_bounds(self, xs, lb, ub):
        return all(self.in_bounds(x, lb, ub) for x in xs)
    
    def printn(self, msg: str) -> None:
        print("\n" + "=" * 50)
        print(msg)
        print("=" * 50)




