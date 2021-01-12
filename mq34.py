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



def ReadChannel(channel_mq):
    adc_mq = spi.xfer2([1, (8 + channel_mq) << 4, 0])
    data_mq = ((adc_mq[1] & 3) << 8) + adc_mq[2]
    return data_mq



Vout_alcohol_mq4= ReadChannel(channel_mq4)
Vout_alcohol_mq3= ReadChannel(channel_mq3)

def MQCalibration_mq(Vout_alcohol_mq):
    val_alcohol = 0.0
    for i in range(50):  # take 50 samples
        val_alcohol += Vout_alcohol_mq
        time.sleep(0.2)
    val_alcohol = val_alcohol / 50
    Sensor_alcohol = val_alcohol * (5.0 / 1023.0)
    Rs_air_alcohol = RL_alcohol * (Vin - Sensor_alcohol) / (Sensor_alcohol)
    # 60.0 was retrieved from the datasheet of MQ3 gas sensor when sensor
    # resistance at is 0.4mg/L of alcohol in the clean air.
    return Rs_air_alcohol
Rs__air_alcohol_mq3 = MQCalibration_mq(Vout_alcohol_mq3)
Ro_alcohol= Rs__air_alcohol_mq3/60
Rs__air_alcohol_mq4 = MQCalibration_mq(Vout_alcohol_mq4)
Ro_methane= Rs__air_alcohol_mq4/4.5

def runController(Ro_alcohol, Ro_methane):
    #Vout_alcohol = Read()
    #Vout_methane = read_mq4()
    Rs_alcohol = RL_alcohol * (Vin * 1023 / Vout_alcohol_mq3 - 1)
    Rs_methane = RL_methane * (Vin * 1023 / Vout_alcohol_mq4 - 1)
    Rs_Ro_Ratio_alcohol = Rs_alcohol / Ro_alcohol
    Rs_Ro_Ratio_methane = Rs_methane / Ro_methane
    Alcohol = 532 * pow(10, (-0.2796 - math.log10(
        Rs_Ro_Ratio_alcohol)) / 0.6413)  # Refer to https://www.nap.edu/read/5435/chapter/11| 1 ppm = 0.00188 mg/L
    Methane = pow(10, (1.0839 - math.log10(
        Rs_Ro_Ratio_methane)) / 0.3601)
    print('Alcohol = {0:0.4f} ppm'.format(Alcohol), ';', 'Rs = {0:0.4f} kohm'.format(Rs_alcohol))
    print('Methane = {0:0.4f} ppm'.format(Methane), ';', 'Rs = {0:0.4f} kohm'.format(Rs_methane))
    return Alcohol, Methane

while True:
    f = open('Result.txt', 'w+')
    try:
        Alcohol_test,Methane_test= runController(Ro_alcohol, Ro_methane)
       
        now_time = time.time()
        Time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        f.write('\nTest_Time:%s' % Time)
        f.write('\nAlcohol_test:%p' % Alcohol_test)
        f.write('\nMethane_test:%p' % Methane_test)
        N= N+1

        time.sleep(3)

    except KeyboardInterrupt:
        exit()
