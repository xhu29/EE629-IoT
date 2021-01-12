import time
import spidev
import math
import httplib
import urllib
key = "6FC69MM5560TGGKH" #API key for ThingSpeak Channel

# Assign MCP3008 channel to each sensor
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

def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


Vout_alcohol = ReadChannel(channel_mq3)
Vout_methane = ReadChannel(channel_mq4)


# Calibrate each sensor in clean air
## Calibrate mq3 sensor
def MQCalibration_mq3():
    val_alcohol = 0.0
    for i in range(50):  # take 50 samples
        val_alcohol += Vout_alcohol
        time.sleep(0.2)
    val_alcohol = val_alcohol / 50
    Sensor_alcohol = val_alcohol * (5.0 / 1023.0)
    Rs_air_alcohol = RL_alcohol * (Vin - Sensor_alcohol) / (Sensor_alcohol)
    Ro_alcohol = Rs_air_alcohol / 60  # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor
    # resistance at is 0.4mg/L of alcohol in the clean air.
    print('Ro_alcohol = {0:0.4f} kohm'.format(Ro_alcohol))
    return Ro_alcohol


## Calibrate mq4 sensor
def MQCalibration_mq4():
    val_methane = 0.0
    for i in range(50):  # take 50 samples
        val_methane += Vout_methane
        time.sleep(0.2)
    val_methane = val_methane / 50
    Sensor_methane = val_methane * (5.0 / 1023.0)
    Rs_air_methane = RL_methane * (Vin - Sensor_methane) / (Sensor_methane)
    Ro_methane = Rs_air_methane / 4.5
    print('Ro_methane= {0:0.4f} kohm'.format(Ro_methane))
    return Ro_methane


def runController(Ro_alcohol, Ro_methane):
    Vout_alcohol = ReadChannel(channel_mq3)
    Vout_methane = ReadChannel(channel_mq4)
    Rs_alcohol = RL_alcohol * (Vin * 1023 / Vout_alcohol - 1)
    Rs_methane = RL_methane * (Vin * 1023 / Vout_methane - 1)
    Rs_Ro_Ratio_alcohol = Rs_alcohol / Ro_alcohol
    Rs_Ro_Ratio_methane = Rs_methane / Ro_methane
    Alcohol = 532 * pow(10, (-0.2796 - math.log10(
        Rs_Ro_Ratio_alcohol)) / 0.6413)  # Refer to https://www.nap.edu/read/5435/chapter/11| 1 ppm = 0.00188 mg/L
    Methane = pow(10, (1.0839 - math.log10(
        Rs_Ro_Ratio_methane)) / 0.3601)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol), ';', 'Methane = {0:0.4f} ppm'.format(Methane))
    return Alcohol, Methane


Ro_alcohol = MQCalibration_mq3()
Ro_methane = MQCalibration_mq4()

while True:
    f = open('Result.txt', 'w+')
    try:
        Alcohol_test, Methane_test = runController(Ro_alcohol, Ro_methane)
        now_time = time.time()
        Time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        f.write('\nTest_Time:%s' % Time)
        f.write('\nAlcohol_test:%0.4f' % Alcohol_test)
        f.write('\nMethane_test:%0.4f' % Methane_test)
        time.sleep(3)

    except KeyboardInterrupt:
        exit()

