import dataclasses

from pathlib import Path
import numpy as np

try:
    import tomllib
except Exception:
    import tomli as tomllib

# ------------------------------ Constants ------------------------------
if "__file__" in globals():
    BASE_DIR = Path(__file__).resolve().parent # scripting directory
else:
    BASE_DIR = Path.cwd()

CONFIG_PATH: Path = BASE_DIR / "_config.toml"
RUNS_DIR: Path = BASE_DIR / "..."

# ------------------------------ Configs ------------------------------

@dataclasses.dataclass
class IOConfig:
    filename_input: str
    filename_output: str
    filename_temp: str

@dataclasses.dataclass
class SimulationConfig:
    n_simulation: int
    n_repeats: int
    n_init: int
    kernel_type: str
    n_params: int
    length_scale: float
    noise_std: float
    noise_var: float
    lower_bounds: float
    upper_bounds: float
    param_names: str

@dataclasses.dataclass
class GaussianProcessConfig:
    kernel_type: str
    length_scale: float
    noise_std: float
    noise_var: float


@dataclasses.dataclass
class HFSSConfig:
    n_simulation: int
    n_repeats: int
    n_init: int
    n_params: int
    lower_bounds: float
    upper_bounds: float
    param_names: str

@dataclasses.dataclass
class SyntheticTestConfig:
    n_simulation: int
    n_repeats: int
    n_init: int
    n_params: int
    lower_bounds: float
    upper_bounds: float
    param_names: str


@dataclasses.dataclass
class Environment:
    dir_base: Path

@dataclasses.dataclass
class Depends:
    n_gp: Path

@dataclasses.dataclass
class AppConfig:
    io: IOConfig
    #sim: SimulationConfig
    opt: GaussianProcessConfig
    hfss: HFSSConfig
    test: SyntheticTestConfig
    env: Environment
    #dep: Depends

    @staticmethod
    def fromDict(config: dict) -> "AppConfig":
        #io = config["io"]; sim = config["sim"]; opt=config["opt"]; hfss = config["hfss"]; test = config["test"]
        io = config["io"]; opt=config["opt"]; hfss = config["hfss"]; test = config["test"]

        dir_base = BASE_DIR
        #n_gp = sim["n_simulation"] - sim["n_init"] 

        env = Environment(
            dir_base=dir_base
        )

        #dep = Depends(
        #    n_gp=n_gp
        #)



        return AppConfig(
            io=IOConfig(**io),
            #sim = SimulationConfig(**sim),
            opt = GaussianProcessConfig(**opt),
            hfss = HFSSConfig(**hfss),
            test = SyntheticTestConfig(**test),
            env = env,
            #dep = dep
        )

# ------------------------------ App ------------------------------
def _loadConfig(path: Path = None) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)

def printConfig(cfg: AppConfig):
    for name, data_obj in cfg.__dict__.items():
        if not dataclasses.is_dataclass(data_obj):
            continue
        header = name.replace('_', ' ').title()
        print(f"\n[{header}]")
        for field in dataclasses.fields(data_obj):
            key = field.name
            value = getattr(data_obj, key)
            if isinstance(value, np.ndarray):
                print(f"  {key:<20}: ndarray(shape={value.shape}, dtype={value.dtype})")
            else:
                if isinstance(value, float):
                    print(f"  {key:<20}: {value:.6f}")
                else:
                    print(f"  {key:<20}: {value}")

def initParams(_config: dict, debug: bool = True, runs_dir: Path | str = RUNS_DIR) -> None:
    cfg = AppConfig.fromDict(_config)
    if debug:
        printConfig(cfg)
    return cfg