import time
import spidev

channel = 0  # Channel '0' is for MQ3(alcohol) gas sensor.

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensor
Vin = 5
Sample_Times = 50 # Determine how many samples will be taken in the calibration phase
RL = 200  # define the load resistance on the board, in kilo ohms
#RO = 10  # Assume that RO equals to 10. Theoretically, it should be gained by calibrating the sensor in clean air.


def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data


# Function to read sensor connected to MCP3008 and calibrate the sensor
def readMQ():
    Vout = ReadChannel(channel)
    for i in range (Sample_Times):
        Vout += ReadChannel(channel)
    return Vout
    Vout1 = Vout / Sample_Times
    sensor_volt = Vout1 / 1024 * 5
    Rs_air = RL * (5.0 - sensor_volt) / sensor_volt
    Ro = Rs_air / 60.0
    print('Ro = {0:0.4f} Kiloohme'.format(Ro))

# Controller main function
def runController():
    Vout = readMQ()
    sensor_volt = Vout1 / 1024 * 5
    Rs= RL*(5.0 - sensor_volt) / sensor_volt
    Rs_Ro_ratio = Rs/Ro

def MQGetPercentage(self, Rs_Ro_ratio, pcurve):
    self.AlcoholCurve = [-1, 0.3424, -0.6316]
        return math.pow(10, (((math.log(Rs_Ro_ratio) - pcurve[1]) / pcurve[2]) + pcurve[0]))

    print('Concentration = {0:0.4f} ppm'.format(Vout), ';', 'Rs = {0:0.4f} kohm'.format(Rs))


while True:
    try:
        runController()
        time.sleep(3)
    except KeyboardInterrupt:
        exit()
