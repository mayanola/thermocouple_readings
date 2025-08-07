
## Single lead readout
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
tc_channel = "AIN0"     # thermocouple channel

# Setup LabJack
handle = ljm.openS("T7", "USB", "ANY")
tc = thermocouples['T']

# CSV File
with open(log_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Voltage (mV)", "CJ Temp (°C)", "TC Temp (°C)"])

# Setup Plot
plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], linestyle='None', marker='o', label="Thermocouple Temp (°C)")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Thermocouple Temperature")
ax.grid(True)
ax.legend()

timestamps = []
temperatures = []

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
            voltage_mV = ljm.eReadName(handle, tc_channel) * 1000
            cj_temp_K = ljm.eReadName(handle, "TEMPERATURE_DEVICE_K")
            cj_temp_C = cj_temp_K - 273.15
            tc_temp_C = tc.inverse_CmV(voltage_mV, Tref=cj_temp_C)
        except Exception as e:
            print(f"Read error: {e}")
            voltage_mV = float('nan')
            cj_temp_C = float('nan')
            tc_temp_C = float('nan')

        # Log to CSV 
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now.strftime("%H:%M:%S"), f"{voltage_mV:.3f}", f"{cj_temp_C:.2f}", f"{tc_temp_C:.2f}"])

        # Update Plot 
        timestamps.append(now.strftime("%H:%M:%S"))
        temperatures.append(tc_temp_C)
 
        # X-axis will be time in seconds since start
        x_vals = [i * log_interval for i in range(len(temperatures))]

        line.set_xdata(x_vals)
        line.set_ydata(temperatures)

        ax.set_xlim(0, duration)
        ax.set_xticks(range(0, duration + 1, 30))  # show ticks every 10 seconds

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

# %%
