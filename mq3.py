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
RO = 10 #Assume that RO equals to 10. Theoretically, it should be gained by calibrating the sensor in clean air.
def ReadChannel(channel):
    adc = spi.xfer2([1, (8+channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# Function to read sensor connected to MCP3008
def readMQ():
    Vout = ReadChannel(channel)
    return Vout

#Calibrate the sensor
def MQCalibration():
    val = 0.0
    for i in range(50): #take 50 samples
        val += readMQ()
        time.sleep (0.5)
        val = val/50 #calculate the average value
        Rs_air = RL*(Vin - val/1024*Vin)/(val/1024*Vin)
        Ro = Rs_air/60.0
        print ('Ro = {0:0.4f} kohm'.format(Ro))
        return val
  
# Controller main function
def runController():
    Vout = readMQ()
    Rs = RL*(Vin*1023/Vout - 1)
    Rs_Ro_Ratio = Rs/Ro
    Alcohol = math.pow(10, (((math.log(Rs_Ro_ratio) + 0.2891)/0.6316)) # The approximately linear regression obtained from the curve on datasheet of each sensor
    print('Concentration = {0:0.4f} mg/L'.format(Alcohol), ';','Rs = {0:0.4f} kohm'.format(Rs))
    

while True:
        try:
        MQCalibration()                            
        runController()
        time.sleep(3)
    except KeyboardInterrupt:
        exit()
