#Some codes were retrieved from https://github.com/kevinwlu/iot/blob/master/lesson7/rpi_spreadsheet.py
import time
import spidev
import math
import json
import sys
import gspread
import psutil
#import datetime
#from system_info import get_temperature
from oauth2client.service_account import ServiceAccountCredentials
GDOCS_OAUTH_JSON       = 'machine-olfactory-project-acd23fe11193.json'
GDOCS_SPREADSHEET_NAME = 'Machine Olfactory Project'
FREQUENCY_SECONDS      = 5

def login_open_sheet(oauth_key_file, spreadsheet):
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, 
                      scopes = ['https://spreadsheets.google.com/feeds',
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
    Rs_alcohol = RL_alcohol * (4.99 * 1023 / Vout_alcohol - 1)
    Rs_methane = RL_methane * (4.99 * 1023 / Vout_methane - 1)
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
    if worksheet is None:
        worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
    
    try:
        Alcohol_test, Methane_test = runController(Ro_alcohol, Ro_methane)
        Time = datetime.datetime.now()
        worksheet.append_row((str(Time), Alcohol_test, Methane_test))

    except:
        print('Append error, logging in again')
        worksheet = None
        time.sleep(FREQUENCY_SECONDS)
        continue
    print('Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME))
    time.sleep(FREQUENCY_SECONDS)

