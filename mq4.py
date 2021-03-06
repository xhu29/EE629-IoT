import time
import spidev
import math

#channel_Alcohol = 0  # Channel '0' is for MQ3(alcohol) gas sensor.
channel_Methane = 2 # Channel '2' is for MQ4 (Methane & CNG) gas sensor.

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensor
Vin = 5
RL = 20  # define the load resistance on the board, in kilo ohms


def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Function to read sensor connected to MCP3008
def readMQ():
    Vout_Methane = ReadChannel(channel_Methane)
    return  Vout_Methane


# Calibrate the sensor
def MQCalibration():
    val = 0.0
    for i in range(50):  # take 50 samples
        val += readMQ()
        time.sleep(0.2)
    val = val / 50  # calculate the average value
    Sensor_val = val*(5.0/1023.0) #convert the analog values to voltage
    Rs_air = RL * (Vin - Sensor_val) / Sensor_val
    Ro = Rs_air / 4.5  # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor resistance at is 0.4mg/L of alcohol in the clean air.
    print('Ro = {0:0.4f} kohm'.format(Ro))
    return Ro


# Controller main function
def runController(Ro):
    Vout = readMQ()
    Vout_vol = Vout*(5.0/1023.0) #convert the analog values to voltage
    Rs = RL * (Vin - Vout_vol)/Vout_vol
    Rs_Ro_Ratio = Rs / Ro
    Methane = pow(10, (1.0839 - math.log10(Rs_Ro_Ratio)) / 0.3601)  
    print('Methane = {0:0.4f} ppm'.format(Methane), ';', 'Rs = {0:0.4f} kohm'.format(Rs))


Ro = MQCalibration()
while True:
    try:
        runController(Ro)
        time.sleep(3)

    except KeyboardInterrupt:
        exit()
