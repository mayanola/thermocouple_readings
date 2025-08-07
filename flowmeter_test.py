
# TESTING FLOWMETER WITH LABJACK T7
# Download and install LabJack Python library from https://support.labjack.com/docs/python-for-ljm-windows-mac-linux
# Wire flowmeter into FIO0

# %%
from labjack import ljm

# Open first found LabJack
handle = ljm.openS("ANY", "ANY", "ANY")
info = ljm.getHandleInfo(handle)
print("Opened LabJack Device Type: %i, Serial: %i" % (info[0], info[2]))

# Sensor Info - change to your specific sensor 
k_factor = 98  # Pulses per liter for Gredia R401
freqDIO = 0

# Clock and Frequency In setup
clockDivisor = 1
clockRollValue = 0
freqIndex = 3      # Rising-to-rising
freqConfigA = 0    # Continuous mode

# Configure clock
ljm.eWriteName(handle, "DIO_EF_CLOCK0_DIVISOR", clockDivisor)
ljm.eWriteName(handle, "DIO_EF_CLOCK0_ROLL_VALUE", clockRollValue)

# Configure Frequency In on selected DIO pin
ljm.eWriteName(handle, "DIO%d_EF_INDEX" % freqDIO, freqIndex)
ljm.eWriteName(handle, "DIO%d_EF_CLOCK_SOURCE" % freqDIO, 0)
ljm.eWriteName(handle, "DIO%d_EF_CONFIG_A" % freqDIO, freqConfigA)
ljm.eWriteName(handle, "DIO%d_EF_ENABLE" % freqDIO, 1)

# Enable clock 
ljm.eWriteName(handle, "DIO_EF_CLOCK0_ENABLE", 1)

# Setup 1-second interval
intervalHandle = 1
ljm.startInterval(intervalHandle, 1000000)

# Read frequency values 
readNames = ["DIO%d_EF_READ_A" % freqDIO, "DIO%d_EF_READ_B_F" % freqDIO]

# Run for 600 seconds
for i in range(600):
    ljm.waitForNextInterval(intervalHandle)
    ljm.eReadName(handle, readNames[0])  # Trigger update of READ_B_F
    freqHz = ljm.eReadName(handle, readNames[1])
    flow_lpm = freqHz / k_factor
    print("Measured Frequency: %.3f Hz | Flow: %.3f L/min" % (freqHz, flow_lpm))

# Clean up
ljm.cleanInterval(intervalHandle)

# Disable output
ljm.eWriteNames(handle, 3, 
    ["DIO_EF_CLOCK0_ENABLE", "DIO%d_EF_ENABLE" % freqDIO, "DAC1_FREQUENCY_OUT_ENABLE"],
    [0, 0, 0])

ljm.close(handle)

# %% If interrupted, run the following cleanup code 

# Clean up
ljm.cleanInterval(intervalHandle)

# Disable output
ljm.eWriteNames(handle, 3, 
    ["DIO_EF_CLOCK0_ENABLE", "DIO%d_EF_ENABLE" % freqDIO, "DAC1_FREQUENCY_OUT_ENABLE"],
    [0, 0, 0])

ljm.close(handle)