from mq import *
import sys, time

try:
    print("Press CTRL+C to abort.")
    
    mq = MQ();
    while True:
        perc = mq.MQPercentage()
        sys.stdout.write("\r")
        sys.stdout.write("\033[K")
        sys.stdout.write("Alcohol: %g ppm" % (perc["GAS_Alcohol"]))
        sys.stdout.flush()
        time.sleep(3)

except:
    print("\nAbort by user")
