import time
import spidev
import math

channel = 0  # Channel '0' is for MQ3(alcohol) gas sensor.

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensor
Vin = 5.0
RL = 200  # define the load resistance on the board, in kilo ohms


#def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Function to read sensor connected to MCP3008
def readMQ():
    Vout = ReadChannel(channel)
    return Vout


# Calibrate the sensor
def MQCalibration():
    val = 0.0
    for i in range(50):  # take 50 samples
        val += readMQ()
        time.sleep(0.2)
    val = val / 50.0  # calculate the average value
    Sensor_val = val*(5.0/1023.0) #convert the analog values to voltage
    Rs_air = RL * (Vin - Sensor_val) / Sensor_val
    Ro = Rs_air / 60.0
    print('Ro = {0:0.4f} kohm'.format(Ro))
    return Ro


# Controller main function
def runController(Ro):
    Vout = readMQ()
    Vout_vol = Vout*(4.9950/1023.0) #convert the analog values to voltage
    Rs = RL * (Vin - Vout_vol)/Vout_vol
    Rs_Ro_Ratio = float (Rs)/float (Ro)
    Alcohol = 532 * pow(10, (-0.2796 - math.log10(Rs_Ro_Ratio))/0.6413)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol), ';', 'Rs_Ro_Ratio = {0:0.4f} kohm'.format(Rs_Ro_Ratio),';''Vout_vol = {0:0.4f} v'.format(Vout_vol))

Ro = MQCalibration()
while True:
    try:
        runController(Ro)
        time.sleep(3)

    except KeyboardInterrupt:
        exit()
