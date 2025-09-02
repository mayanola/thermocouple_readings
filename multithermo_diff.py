import time
import csv
from datetime import datetime
from labjack import ljm
from thermocouples_reference import thermocouples
import matplotlib.pyplot as plt

# ---------------- Settings ----------------
log_file = "temperature_log_diff_multi.csv"
duration = 300           # total run time in seconds
log_interval = 1         # seconds

# Define thermocouple differential pairs: [(pos, neg), ...]
# Example: 3 thermocouples wired AIN0–AIN1, AIN2–AIN3, AIN4–AIN5
tc_pairs = [(0, 1), (2, 3), (4, 5)]

# Open LabJack
handle = ljm.openS("T7", "USB", "ANY")

# Configure differential mode for each positive channel
for pos, neg in tc_pairs:
    ljm.eWriteName(handle, f"AIN{pos}_NEGATIVE_CH", neg)
    ljm.eWriteName(handle, f"AIN{pos}_RANGE", 0.1)   # ±0.1 V for better resolution
    ljm.eWriteName(handle, f"AIN{pos}_RESOLUTION_INDEX", 8)

# Thermocouple type
tc = thermocouples["T"]

# ---------------- CSV Setup ----------------
with open(log_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    header = ["Timestamp", "CJ Temp (°C)"]
    for pos, neg in tc_pairs:
        header += [f"AIN{pos}-AIN{neg} Voltage (mV)", f"AIN{pos}-AIN{neg} Temp (°C)"]
    writer.writerow(header)

# ---------------- Plot Setup ----------------
plt.ion()
fig, ax = plt.subplots()
lines = [ax.plot([], [], marker="o", label=f"AIN{pos}-AIN{neg}")[0] for pos, neg in tc_pairs]
ax.set_xlabel("Time (s)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Differential Thermocouple Temperatures")
ax.grid(True)
ax.legend()

# Data storage
x_vals = []
temp_data = {f"{pos}-{neg}": [] for pos, neg in tc_pairs}

# ---------------- Main Loop ----------------
start_time = time.time()
try:
    while True:
        elapsed = time.time() - start_time
        if elapsed > duration:
            break

        now = datetime.now()

        # Cold junction compensation
        try:
            cj_temp_K = ljm.eReadName(handle, "TEMPERATURE_DEVICE_K")
            cj_temp_C = cj_temp_K - 273.15
        except Exception as e:
            print(f"CJ read error: {e}")
            cj_temp_C = float("nan")

        row = [now.strftime("%H:%M:%S"), f"{cj_temp_C:.2f}"]

        # Loop over each thermocouple pair
        for pos, neg in tc_pairs:
            ch_key = f"{pos}-{neg}"
            try:
                voltage_mV = ljm.eReadName(handle, f"AIN{pos}") * 1000  # differential
                tc_temp_C = tc.inverse_CmV(voltage_mV, Tref=cj_temp_C)
            except Exception as e:
                print(f"Read error AIN{pos}-AIN{neg}: {e}")
                voltage_mV, tc_temp_C = float("nan"), float("nan")

            row += [f"{voltage_mV:.3f}", f"{tc_temp_C:.2f}"]
            temp_data[ch_key].append(tc_temp_C)

        # Write CSV
        with open(log_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(row)

        # Update plot
        x_vals.append(int(elapsed))
        for (pos, neg), line in zip(tc_pairs, lines):
            ch_key = f"{pos}-{neg}"
            line.set_xdata(x_vals)
            line.set_ydata(temp_data[ch_key])

        ax.set_xlim(0, duration)
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
    print(f"\nLogging complete. Data saved to: {log_file}")

