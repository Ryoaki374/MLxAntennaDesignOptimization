import os
import time
import csv
import json
import ScriptEnv

# --- Initialize the Scripting Environment ---
ScriptEnv.Initialize("Ansoft.ElectronicsDesktop")

# --- Configuration & Global Constants ---
LOG_PATH = r"T:\RAkizawa\HFSS_C2R\output_log.txt"
CONFIG_PATH = r'T:\RAkizawa\HFSS_C2R\_config_HFSS.json'

# --- parameter definition ---

def printlog(message):
    """Writes a simple message to the log file."""
    try:
        with open(LOG_PATH, "a") as f:
            f.write(str(message) + "\n")
    except Exception as e:
        with open(LOG_PATH, "a") as f:
            f.write("[ERROR][printlog] {}".format(str(e)))

# Clear the log file at the start of the script for a clean debug session
if os.path.exists(LOG_PATH):
    os.remove(LOG_PATH)
printlog("--- HFSS Subroutine Script Initialized ---")


# --- Load Settings from Config File ---
try:
    printlog("Loading configuration from: {}".format(CONFIG_PATH))
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    WATCH_DIR = config['WATCH_DIR']
    INPUT_FILE = config['INPUT_FILE']
    RESULTS_FILE = config['RESULTS_FILE']
    PARAM_KEYS = config['param_names']
    
    # Simulation counts
    TOTAL_SIMULATIONS_TO_RUN = config["n_simulation"] * config["n_repeats"]
    printlog("Configuration loaded. WATCH_DIR: {}. Total Runs: {}".format(WATCH_DIR, TOTAL_SIMULATIONS_TO_RUN))
except Exception as e:
    printlog("[ERROR][loading config] {}".format(e))
    exit()

# Create the folder if it does not exist
if not os.path.exists(WATCH_DIR):
    printlog("[ERROR][Watching dir] Creating: {}".format(WATCH_DIR))
    os.makedirs(WATCH_DIR)

# --- HFSS Object Initialization ---
try:
    oProject = oDesktop.GetActiveProject()
    oDesign = oProject.GetActiveDesign()
    oOptiModule = oDesign.GetModule("Optimetrics")
    oReportModule = oDesign.GetModule("ReportSetup")
    printlog("HFSS Objects Initialized: Project='{}', Design='{}'".format(oProject.GetName(), oDesign.GetName()))
except AttributeError:
    printlog("[ERROR][HFSS_init] Could not get active Project or Design.")
    exit()

def runSimulation(input_csv_path):
    setup_name = "ParametricSetup_FromScript"
    report_name = "S11_Export_Report"
    temp_export_path = os.path.join(WATCH_DIR, "temp_hfss_export.csv")
    
    # s11_value = None

    try:
        printlog("[State] Importing parametric setup from: {}".format(INPUT_FILE))
        oOptiModule.ImportSetup("OptiParametric", 
            [
                "NAME:{}".format(setup_name), 
                input_csv_path
            ])

        oProject.Save()
        oOptiModule.SolveSetup(setup_name)
        printlog("[State] Solve complete.")

        # --- 3. Create Report and Export Data ---
        oReportModule = oDesign.GetModule("ReportSetup")

        if report_name in oReportModule.GetAllReportNames():
            printlog("[State] Deleting existing report: {}".format(report_name))
            oReportModule.DeleteReports([report_name])

        printlog("[State] Creating report: {}".format(report_name))
        oReportModule.CreateReport(report_name, "Modal Solution Data", "Rectangular Plot", "Setup1 : Sweep", 
                                   ["Domain:=", "Sweep"], 
                                   ["Freq:=", ["All"], "s1x:=", ["All"], "s1y:=", ["All"], "s2x:=", ["All"], "s2y:=", ["All"], "s3x:=", ["All"], "s3y:=", ["All"], "s4x:=", ["All"], "s4y:=", ["All"]], 
                                   ["X Component:=", "Freq", "Y Component:=", ["db(mean(mag(S(R:1,R:1))))"]])


        printlog("[State] Exporting report to temporary file: {}".format(temp_export_path))
        oReportModule.ExportToFile(report_name, temp_export_path, False)

    except Exception as e:
        printlog("[ERROR] HFSS simulation: {}".format(e))
        return None
        
    finally:
        # --- 5. Clean up HFSS project for the next run ---
        printlog("[State] Cleaning up a current HFSS simulation...")
        try:
            if oDesign:
                
                if setup_name in oOptiModule.GetSetupNames():
                    oOptiModule.DeleteSetups([setup_name])
                if report_name in oReportModule.GetAllReportNames():
                    oReportModule.DeleteReports([report_name])
    
                oDesign.DeleteFullVariation("All", False)
                
                printlog("[State] Successfully cleaned up")
        except Exception as cleanup_e:
            printlog("[ERROR] HFSS object cleanup: {}".format(cleanup_e))

    
# --- Main Loop ---
printlog("[State] Entering main loop...")
simulations_run = 0

while simulations_run < TOTAL_SIMULATIONS_TO_RUN:
    if os.path.exists(INPUT_FILE):
        printlog("Run {}/{}: Detected {}".format(simulations_run + 1, TOTAL_SIMULATIONS_TO_RUN, INPUT_FILE))

        time.sleep(0.2)
        current_params = {}

        # 1. Read Input
        try:
            with open(INPUT_FILE, 'r') as f:
                reader = csv.DictReader(f) # DictReader uses the header row automatically
                current_params = next(reader) 

            printlog("[State] Successfully read parameters: {}".format(current_params))

        except Exception as e:
            printlog("[ERROR] Failed to read or parse {}. Exception: {}".format(INPUT_FILE, e))
            try:
                os.remove(INPUT_FILE)
            except:
                pass
            continue
        
        # 2. Run Simulation
        start_time = time.time()
        runSimulation(INPUT_FILE)
        duration = time.time() - start_time

        try:
            os.remove(INPUT_FILE)
        except:
            printlog("[ERROR] Could not delete input file.")

        simulations_run += 1
        
    time.sleep(1)

printlog("--- All Completed ---")
