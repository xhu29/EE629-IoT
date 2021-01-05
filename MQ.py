# The original script was retrieved from https://github.com/kevinwlu/iot/tree/master/lesson3.
# Proper modifications have been made by Xi Hu.
import time
import spidev

# Sensor channel on MCP3008
Alcohol_CHANNEL = 0 #MQ3
#NO2_CHANNEL = 1 #This one should be changed properly later
#CH4_CHANNEL = 2
#LPG_CHANNEL = 3
#CO_CHANNEL = 4
#H2S_CHANNEL = 5
#NH3_CHANNEL = 6
#CO2_CHANNEL = 7

vin = 5
R0 = 10000 # It should be changed properly for different sensors.
RL = 200000

# Conversions based on Rs/Ro vs ppm plots of the sensors
# CO_Conversions = [((0, 100), (0, 0.25)), ((100, 133), (0.25, 0.325)),
#    ((133, 167), (0.325, 0.475)), ((167, 200), (0.475, 0.575)),
#    ((200, 233), (0.575, 0.665)), ((233, 267), (0.666, 0.75))]
# Conversions based on Rs/Ro vs mg/L plots of the MQ3 gas sensor
Alcohol_Conversions = [((0.1, 0.22), (2.2, 1.6)), ((0.22, 0.4), (1.6, 1.0)),
    ((0.4, 1.0), (1.0, 0.53)), ((1.0, 1.7), (0.53, 0.4)),
    ((1.7, 2.6), (0.4, 0.28)), ((2.6, 4), (0.28, 0.2)), 
    ((4, 6), (0.2, 0.16)),((6, 8), (0.16, 0.14)),((8, 10), (0.14, 0.12))]

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)

# Function to read SPI data from MCP3008 chip
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def get_resistance(channel):
    result = ReadChannel(channel)
    if result == 0:
        resistance = 0
    else:
        resistance = (vin/result -1) * RL
    return resistance

def converttoppm(rs, conversions):
    rsper = 100* (float(rs) / R0) # The coefficient '100' may be fine-tuned properly.
    for a in conversions:
        if a[0][0] >= rsper > a[0][1]:
            mid, hi = rsper - a[0][0], a[0][1] - a[0][0]
            sf = float(mid) / hi
            ppm = sf * (a[1][1] - a[1][0]) + a[1][0]
            return ppm
        return 0

def get_Alcohol():
    rs = get_resistance(Alcohol_CHANNEL)
    ppm = converttoppm(rs, Alcohol_Conversions)
    return ppm

#def get_CO():
#    rs = get_resistance(CO_CHANNEL)
#    ppm = converttoppm(rs, CO_Conversions)
#    return ppm

# Controller main function
def runController():
    Alcohol_reading = get_Alcohol()
#    CO_reading = get_CO()
#    print('CO={0:0.5f} ppm  NO2={1:0.5f} ppm'.format(CO_reading, NO2_reading))
    print('Alcohol={:0.5f} mg/L'.format(Alcohol_reading))

while True:
    runController()
    time.sleep(3)
