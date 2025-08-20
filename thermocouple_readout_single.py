
## Multiple lead readout
# Negative in GND and positive in AIN0

# %% Test readout for 5 minutes

import time
import csv
from datetime import datetime
from labjack import ljm
from thermocouples_reference import thermocouples
import matplotlib.pyplot as plt
import pandas as pd

# General Settings
log_file = "temperature_log.csv"
duration = 300           # total run time in seconds
log_interval = 1        # how often to log (seconds)
#tc_channels = [f"AIN{i}" for i in range(14)]    # thermocouple channels
                                                # can use 0 through to 13 because single readout not differential (all Analog INputs relative to ground)
tc_channels = [f"AIN{i}" for i in range(2)]     #only 3 thermocouples hooked up currently

handle = ljm.openS("T7", "USB", "ANY")
tc = thermocouples["T"]

# CSV File Setup
with open(log_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    header = ["Timestamp", "CJ Temp (°C)"]
    for ch in tc_channels:
        header.append(f"{ch} Voltage (mV)")
        header.append(f"{ch} Temp (°C)")
    writer.writerow(header)

# Setup Plot
plt.ion()
fig, ax = plt.subplots()
lines = [ax.plot([], [], marker='o', label=ch)[0] for ch in tc_channels]
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Thermocouple Temperature")
ax.grid(True)
ax.legend()

timestamps = []
temp_data = {ch: [] for ch in tc_channels}

# Logging Loop
start_time = time.time()
try:
    while True:
        elapsed = time.time() - start_time
        if elapsed > duration:
            break

        now = datetime.now()

        # Read LabJack Data 
        try:
            cj_temp_K = ljm.eReadName(handle, "TEMPERATURE_DEVICE_K")
            cj_temp_C = cj_temp_K - 273.15
        except Exception as e:
            print(f"Read error: {e}")
            voltage_mV = float('nan')
            cj_temp_C = float('nan')
            tc_temp_C = float('nan')
        
        # Create respective row
        row = [now.strftime("%H:%M:%S"), f"{cj_temp_C:.2f}"]

        # Log data for each channel
        for ch in tc_channels:
            try:
                voltage_mV = ljm.eReadName(handle, ch) * 1000
                tc_temp_C = tc.inverse_CmV(voltage_mV, Tref=cj_temp_C)
            except Exception as e:
                print(f"Read error on {ch}: {e}")
                voltage_mV, tc_temp_C = float("nan"), float("nan")

            row.append(f"{voltage_mV:.3f}")
            row.append(f"{tc_temp_C:.2f}")
            temp_data[ch].append(tc_temp_C)

        # Log to CSV 
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)


        # Update Plot 
        x_vals = [i * log_interval for i in range(len(temp_data[tc_channels[0]]))]       # X-axis will be time in seconds since start
        for ch, line in zip(tc_channels, lines):
                  line.set_xdata(x_vals)
                  line.set_ydata(temp_data[ch])

        ax.set_xlim(0, duration)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()

        time.sleep(log_interval)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    ljm.close(handle)
    plt.ioff()
    plt.show()
    print(f"\nLogging complete. Data saved to: {log_file}")

