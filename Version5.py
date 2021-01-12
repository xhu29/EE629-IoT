# Some codes were retrieved from https://github.com/kevinwlu/iot/blob/master/lesson7/rpi_spreadsheet.py
import time
import spidev
import math
import json
import sys
import gspread
import psutil
import datetime
# from system_info import get_temperature
from oauth2client.service_account import ServiceAccountCredentials

GDOCS_OAUTH_JSON = 'machine-olfactory-project-acd23fe11193.json'
GDOCS_SPREADSHEET_NAME = 'Machine Olfactory Project'
FREQUENCY_SECONDS = 5


def login_open_sheet(oauth_key_file, spreadsheet):
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file,
                                                                       scopes=['https://spreadsheets.google.com/feeds',
                                                                               'https://www.googleapis.com/auth/drive'])
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print('Unable to login and get spreadsheet. Check OAuth credentials, spreadsheet name, and')
        print('make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)


print('Logging sensor measurements to {0} every {1} seconds.'.format(GDOCS_SPREADSHEET_NAME, FREQUENCY_SECONDS))
print('Press Ctrl-C to quit.')
worksheet = None

# Assign MCP3008 channel to each sensor
channel_mq3 = 0  # Channel '0' is for MQ3(alcohol) gas sensor.
# Channels for other sensors were assigned in a similar fashion
channel_mq4 = 1  # Methane
channel_mq6 = 2  # Butane
channel_mq7 = 3  # Carbon Monoxide
channel_mq136 = 5  # Hydrogen Sulfide
# channel_mq137 =
# channel_mg811 =

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensors
Vin = 5.0
RL_alcohol = 200  # Determine the load resistance on the board, in kilo ohms
RL_methane_butane_H2S = 20  # Methane, butane, and hydrogen sulfide sensors have the same RL value.
RL_CO = 10


# RL_NH3 = 47

# Function to read SPI data from MCP3008 chip
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Function to read sensor connected to MCP3008
## Read sensor mq3
def ReadMq3():
    Vout_alcohol = ReadChannel(channel_mq3)
    return Vout_alcohol

## Read sensor mq4
def ReadMq4():
    Vout_methane = ReadChannel(channel_mq4)
    return Vout_methane

## Read sensor mq6
def ReadMq6():
    Vout_butane = ReadChannel(channel_mq6)
    return Vout_butane

## Read sensor mq7
def ReadMq7():
    Vout_CO = ReadChannel(channel_mq7)
    return Vout_CO

## Read sensor mq136
def ReadMq136():
    Vout_H2S = ReadChannel(channel_mq136)
    return Vout_H2S


# Calibrate each sensor in clean air
## Calibrate mq3 sensor
def MQCalibration_mq3():
    val_alcohol = 0.0
    for i in range(50):  # take 50 samples
        val_alcohol += ReadMq3()
        time.sleep(0.2)
    val_alcohol = val_alcohol / 50
    Sensor_alcohol = val_alcohol * (5.0 / 1023.0)
    Rs_air_alcohol = RL_alcohol * (Vin - Sensor_alcohol) / Sensor_alcohol
    Ro_alcohol = Rs_air_alcohol / 60  # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor
    # resistance at is 0.4mg/L of alcohol in the clean air.
    print('Ro_alcohol = {0:0.4f} kohm'.format(Ro_alcohol))
    return Ro_alcohol


## Calibrate mq4 sensor
def MQCalibration_mq4():
    val_methane = 0.0
    for i in range(50):  # take 50 samples
        val_methane += ReadMq4()
        time.sleep(0.2)
    val_methane = val_methane / 50
    Sensor_methane = val_methane * (5.0 / 1023.0)
    Rs_air_methane = RL_methane_butane_H2S * (Vin - Sensor_methane) / Sensor_methane
    Ro_methane = Rs_air_methane / 4.5
    print('Ro_methane= {0:0.4f} kohm'.format(Ro_methane))
    return Ro_methane


## Calibrate mq6 sensor
def MQCalibration_mq6():
    val_butane = 0.0
    for i in range(50):  # take 50 samples
        val_butane += ReadMq6()
        time.sleep(0.2)
    val_butane = val_butane / 50
    Sensor_butane = val_butane * (5.0 / 1023.0)
    Rs_air_butane = RL_methane_butane_H2S * (Vin - Sensor_butane) / Sensor_butane
    Ro_butane = Rs_air_butane / 10
    print('Ro_butane= {0:0.4f} kohm'.format(Ro_butane))
    return Ro_butane


## Calibrate mq7 sensor
def MQCalibration_mq7():
    val_CO = 0.0
    for i in range(50):  # take 50 samples
        val_CO += ReadMq7()
        time.sleep(0.2)
    val_CO = val_CO / 50
    Sensor_CO = val_CO * (5.0 / 1023.0)
    Rs_air_CO = RL_CO * (Vin - Sensor_CO) / (Sensor_CO)
    Ro_CO = Rs_air_CO / 11.8
    print('Ro_CO= {0:0.4f} kohm'.format(Ro_CO))
    return Ro_CO


## Calibrate mq136 sensor
def MQCalibration_mq136():
    val_H2S = 0.0
    for i in range(50):  # take 50 samples
        val_H2S += ReadMq136()
        time.sleep(0.2)
    val_H2S = val_H2S / 50
    Sensor_H2S = val_H2S * (5.0 / 1023.0)
    Rs_air_H2S = RL_methane_butane_H2S * (Vin - Sensor_H2S) / Sensor_H2S
    Ro_H2S = Rs_air_H2S / 3.6
    print('Ro_H2S= {0:0.4f} kohm'.format(Ro_H2S))
    return Ro_H2S


def runController(Ro_alcohol, Ro_methane, Ro_butane, Ro_CO, Ro_H2S):
    Vout_alcohol = ReadMq3()
    Vout_methane = ReadMq4()
    Vout_butane = ReadMq6()
    Vout_CO = ReadMq7()
    Vout_H2S = ReadMq136()

    Rs_alcohol = RL_alcohol * (4.9950 * 1023 / Vout_alcohol - 1)
    Rs_methane = RL_methane_butane_H2S * (4.9950 * 1023 / Vout_methane - 1)
    Rs_butane = RL_methane_butane_H2S * (4.9950 * 1023 / Vout_butane - 1)
    Rs_CO = RL_CO * (4.9950 * 1023 / Vout_CO - 1)
    Rs_H2S = RL_methane_butane_H2S * (4.9950 * 1023 / Vout_H2S - 1)

    Rs_Ro_Ratio_alcohol = Rs_alcohol / Ro_alcohol
    Rs_Ro_Ratio_methane = Rs_methane / Ro_methane
    Rs_Ro_Ratio_butane = Rs_butane / Ro_butane
    Rs_Ro_Ratio_CO = Rs_CO / Ro_CO
    Rs_Ro_Ratio_H2S = Rs_H2S / Ro_H2S

    Alcohol = 532 * pow(10, (-0.2796 - math.log10(
        Rs_Ro_Ratio_alcohol)) / 0.6413)  # Refer to https://www.nap.edu/read/5435/chapter/11| 1 ppm = 0.00188 mg/L
    Methane = pow(10, (1.0839 - math.log10(
        Rs_Ro_Ratio_methane)) / 0.3601)
    Butane = pow(10, (0.6666 - math.log10(
        Rs_Ro_Ratio_butane)) / 0.1589)
    CO = pow(10, (0.4845 - math.log10(
        Rs_Ro_Ratio_CO)) / 0.2181)
    H2S = pow(10, (0.8169 - math.log10(
        Rs_Ro_Ratio_H2S)) / 0.4019)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol),
          ';', 'Methane = {0:0.4f} ppm'.format(Methane),
          ';', 'Butane = {0:0.4f} ppm'.format(Butane),
          ';', 'CO = {0:0.4f} ppm'.format(CO),
          ';', 'H2S = {0:0.4f} ppm'.format(H2S))
    return Alcohol, Methane, Butane, CO, H2S


Ro_alcohol = MQCalibration_mq3()
Ro_methane = MQCalibration_mq4()
Ro_butane = MQCalibration_mq6()
Ro_CO = MQCalibration_mq7()
Ro_H2S = MQCalibration_mq136()

while True:
    if worksheet is None:
        worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

    try:
        Alcohol_test, Methane_test, Butane_test, CO_test, H2S_test = runController(Ro_alcohol, Ro_methane, Ro_butane,
                                                                                   Ro_CO, Ro_H2S)
        Time = datetime.datetime.now()
        worksheet.append_row((str(Time), Alcohol_test, Methane_test, Butane_test, CO_test, H2S_test))

    except:
        print('Append error, logging in again')
        worksheet = None
        time.sleep(FREQUENCY_SECONDS)
        continue
    #print('Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME))
    time.sleep(FREQUENCY_SECONDS)
