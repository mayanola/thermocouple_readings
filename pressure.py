from labjack import ljm

handle = ljm.openS("T7", "USB", "ANY")

try:
    voltage = ljm.eReadName(handle, "AIN0")

    # convert voltage to PSI
    pressure_psi = (voltage - 0.5) * (30.0 / 4.0)
    if pressure_psi < 0:
        pressure_psi = 0   # clamp (noise below 0.5V)
    
    print(f"Sensor voltage: {voltage:.3f} V")
    print(f"Pressure: {pressure_psi:.2f} PSI")

finally:
    ljm.close(handle)

