import time
import spidev
channel = 0 # Channel '0' is for MQ3(alcohol) gas sensor.

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 976000

# Define basic parameters of the sensor
Vin = 5
RL  = 200    # define the load resistance on the board, in kilo ohms
RO  = 10     # RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
             # which is derived from the chart in datashee
# Function to read SPI data from MCP3008 chip
def ReadChannel(channel):
    adc = spi.xfer2([1, (8+channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# Function to read sensor connected to MCP3008
def readMQ():
    Vout = ReadChannel(channel)
    return Vout
  
# Controller main function
def runController():
    Vout = readMQ()
    Rs = RL*(Vin/Vout - 1)
    print('Concentration = {0:0.4f} ppm'.format(Vout)')
    print('Resistance = {0:0.4f} kohm'.format(Rs)')

while True:
    try:
        runController()
        time.sleep(5)
    except KeyboardInterrupt:
        exit()
