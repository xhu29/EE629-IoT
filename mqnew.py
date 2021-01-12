import time
import spidev
import math

channel_mq3 = 0  # Channel '0' is for MQ3(alcohol) gas sensor.
channel_mq4 = 2  # Channel '2' is for MQ4 (Methane and CNG) gas sensor.

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

def ReadChannel_mq3(channel_mq3):
    adc_mq3 = spi.xfer2([1, (8 + channel_mq3) << 4, 0])
    data_mq3 = ((adc_mq3[1] & 3) << 8) + adc_mq3[2]
    return data_mq3


def ReadChannel_mq4(channel_mq4):
    adc_mq4 = spi.xfer2([1, (8 + channel_mq4) << 4, 0])
    data_mq4 = ((adc_mq4[1] & 3) << 8) + adc_mq4[2]
    return data_mq4


# Function to read sensor connected to MCP3008
def read_mq3():
    Vout_alcohol = ReadChannel_mq3(channel_mq3)
    return Vout_alcohol


def read_mq4():
    Vout_methane = ReadChannel_mq4(channel_mq4)
    return Vout_methane


# Calibrate mq3 sensor
def MQCalibration_mq3():
    val_alcohol = 0.0
    for i in range(50):  # take 50 samples
        val_alcohol += read_mq3()
        time.sleep(0.2)
    val_alcohol = val_alcohol / 50
    Sensor_alcohol = val_alcohol * (5.0 / 1023.0)
    Rs_air_alcohol = RL_alcohol * (Vin - Sensor_alcohol) / (Sensor_alcohol)
    Ro_alcohol = Rs_air_alcohol / 60  # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor
    # resistance at is 0.4mg/L of alcohol in the clean air.
    print('Ro_alcohol = {0:0.4f} kohm'.format(Ro_alcohol))
    return Ro_alcohol


# Calibrate mq4 sensor
def MQCalibration_mq4():
    val_methane = 0.0
    for i in range(50):  # take 50 samples
        val_methane += read_mq4()
        time.sleep(0.2)
    val_methane = val_methane / 50
    Sensor_methane = val_methane * (5.0 / 1023.0)
    Rs_air_methane = RL_methane * (Vin - Sensor_methane) / (Sensor_methane)
    Ro_methane = Rs_air_methane / 4.5
    print('Ro_methane= {0:0.4f} kohm'.format(Ro_methane))
    return Ro_methane


# Controller main function
def runController(Ro_alcohol, Ro_methane):
    global Vout_alcohol, Vout_methane
    Vout_alcohol = read_mq3()
    Vout_methane = read_mq4()
    Rs_alcohol = RL_alcohol * (Vin * 1023 / Vout_alcohol - 1)
    Rs_methane = RL_methane * (Vin * 1023 / Vout_methane - 1)
    Rs_Ro_Ratio_alcohol = Rs_alcohol / Ro_alcohol
    Rs_Ro_Ratio_methane = Rs_methane / Ro_methane
    Alcohol = 532 * pow(10, (-0.2796 - math.log10(
        Rs_Ro_Ratio_alcohol)) / 0.6413)  # Refer to https://www.nap.edu/read/5435/chapter/11| 1 ppm = 0.00188 mg/L
    Methane = pow(10, (1.0839 - math.log10(
        Rs_Ro_Ratio_methane)) / 0.3601)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol), ';', 'Rs = {0:0.4f} kohm'.format(Rs_alcohol))
    print('Methane = {0:0.4f} ppm'.format(Methane), ';', 'Rs = {0:0.4f} kohm'.format(Rs_methane))


Ro_alcohol = MQCalibration_mq3()
Ro_methane = MQCalibration_mq4()
while True:
    try:
        runController(Ro_alcohol, Ro_methane)
        time.sleep(3)

    except KeyboardInterrupt:
        exit()
