import time
import spidev
import math

channel = 0  # Channel '0' is for MQ3(alcohol) gas sensor.
channel = 2  # Channel '2' is for MQ4 (Methane and CNG) gas sensor.

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensors
Vin = 5
RL_alcohol = 200  # define the load resistance on the board, in kilo ohms
RL_methane = 20
# RL_CO = 10
# RL_NH3 = 47

def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Function to read sensor connected to MCP3008
def readMQ(Vout_alcohol, Vout_methane):
    Vout_alcohol = ReadChannel(0)
    Vout_methane = ReadChannel(2)
    return Vout_alcohol, Vout_methane


# Calibrate the sensor
def MQCalibration(Ro_alcohol, Ro_methane):
    val_alcohol = 0.0
    val_methane = 0.0
    for i in range(50):  # take 50 samples
        val_alcohol += readMQ(Vout_alcohol)
        val_methane += readMQ(Vout_methane)
        time.sleep(0.2)
    val_alcohol = val_alcohol / 50
    val_methane = val_methane / 50
    Sensor_alcohol = val_alcohol * (5.0 / 1023.0)
    Sensor_methane = val_methane * (5.0 / 1023.0)
    Rs_air_alcohol = RL_alcohol * (Vin - Sensor_alcohol) / (Sensor_alcohol)
    Rs_air_methane = RL_methane * (Vin - Sensor_methane) / (Sensor_methane)
    Ro_alcohol = Rs_air_alcohol / 60  # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor resistance at is 0.4mg/L of alcohol in the clean air.
    Ro_methane = Rs_air_methane / 4.5
    print('Ro_alcohol = {0:0.4f} kohm'.format(Ro_alcohol), ';', 'Ro_methane= {0:0.4f} kohm'.format(Ro_methane))
    return Ro_alcohol, Ro_methane


# Controller main function
def runController(Ro_alcohol, Ro_methane):
    Vout_alcohol = readMQ(Vout_alcohol)
    Vout_methane = readMQ(Vout_methane)
    Rs_alcohol = RL_alcohol * (Vin * 1023 / Vout_alcohol - 1)
    Rs_methane = RL_methane * (Vin * 1023 / Vout_methane - 1)
    Rs_Ro_Ratio_alcohol = Rs_alcohol / Ro_alcohol
    Rs_Ro_Ratio_methane = Rs_methane / Ro_methane
    Alcohol = 532* pow(10, (-0.2796 - math.log10(
        Rs_Ro_Ratio_alcohol)) / 0.6413)  # Refer to https://www.nap.edu/read/5435/chapter/11| 1 ppm = 0.00188 mg/L
    Methane = pow(10, (1.0839 - math.log10(
        Rs_Ro_Ratio_methane)) / 0.3601)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol), ';', 'Rs = {0:0.4f} kohm'.format(Rs_alcohol))
    print('Methane = {0:0.4f} ppm'.format(Methane), ';', 'Rs = {0:0.4f} kohm'.format(Rs_methane))


Ro_alcohol = MQCalibration(Ro_alcohol, Ro_methane)
Ro_methane = MQCalibration(Ro_alcohol, Ro_methane)
while True:
    try:
        runController(Ro_alcohol, Ro_methane)
        time.sleep(3)

    except KeyboardInterrupt:
        exit()
