## Differential Readout
# Download and install LabJack Python library from https://support.labjack.com/docs/python-for-ljm-windows-mac-linux
# Negative in AIN1 and positive in AIN0

#%% Test readout for 1 minute

import time
import csv
from datetime import datetime
from labjack import ljm
from thermocouples_reference import thermocouples
import matplotlib.pyplot as plt

# Settings
log_file = "temperature_log_diff.csv"
duration = 60           # total run time in seconds
log_interval = 1        # log every second
tc_channel = "AIN0"     # positive thermocouple lead
neg_channel = 1         # negative lead is AIN1

# Setup LabJack
handle = ljm.openS("T7", "USB", "ANY")

# Configure differential mode: AIN0 - AIN1
ljm.eWriteName(handle, "AIN0_NEGATIVE_CH", neg_channel)
ljm.eWriteName(handle, "AIN0_RANGE", 0.1)  # ±0.1 V for better resolution
ljm.eWriteName(handle, "AIN0_RESOLUTION_INDEX", 8)

# Get thermocouple type
tc = thermocouples['T']

# Setup CSV
with open(log_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Voltage (mV)", "CJ Temp (°C)", "TC Temp (°C)"])

# Setup Plot
plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], linestyle='None', marker='o', markersize=5, label="Temp (°C)")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Differential Thermocouple Temperature (AIN0 - AIN1)")
ax.grid(True)
ax.legend()

temperatures = []
x_vals = []

# Main Logging Loop 
start_time = time.time()
try:
    while True:
        elapsed = time.time() - start_time
        if elapsed > duration:
            break

        now = datetime.now()

        try:
            voltage_mV = ljm.eReadName(handle, tc_channel) * 1000  # differential read (AIN0 - AIN1)
            cj_temp_K = ljm.eReadName(handle, "TEMPERATURE_DEVICE_K")
            cj_temp_C = cj_temp_K - 273.15
            tc_temp_C = tc.inverse_CmV(voltage_mV, Tref=cj_temp_C)
            print(f"Temp: {tc_temp_C:.2f} °C")
        except Exception as e:
            print(f"Read error: {e}")
            voltage_mV = cj_temp_C = tc_temp_C = float('nan')

        # Log to CSV
        with open(log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([now.strftime("%H:%M:%S"), f"{voltage_mV:.3f}", f"{cj_temp_C:.2f}", f"{tc_temp_C:.2f}"])

        # Plot
        x_vals.append(int(elapsed))
        temperatures.append(tc_temp_C)

        line.set_xdata(x_vals)
        line.set_ydata(temperatures)
        ax.set_xlim(0, duration)
        ax.set_xticks(range(0, duration + 1, 10))  # X-ticks every 10 sec
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()

        time.sleep(log_interval)

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    ljm.close(handle)
    plt.ioff()
    plt.show()
    print(f"\n Logging complete. Data saved to: {log_file}")

