# retrieved from https://github.com/ControlEverythingCommunity/ADC121C_MQ3/blob/master/Python/ADC121C_MQ3.py
import smbus
import time

# Get I2C bus
bus = smbus.SMBus(1)

# ADC121C_MQ3 address, 0x50(80)
# Read data back from 0x00(00), 2 bytes
# raw_adc MSB, raw_adc LSB
data = bus.read_i2c_block_data(0x50, 0x00, 2)

# Convert the data to 12-bits
raw_adc = (data[0] & 0x0F) * 256 + data[1]
concentration = (9.95 / 4096.0) * raw_adc + 0.05

# Output data to screen
print "Alcohol Concentration : %.2f mg/l" %concentration
