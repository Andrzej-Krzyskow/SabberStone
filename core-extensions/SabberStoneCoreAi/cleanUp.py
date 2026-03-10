# simple cleanup script for the StarCraftGP project

import os
import sys
import time

print ("I hope you saved every file you need, because here I go! But I will actually rename status.xml, if I find it.")

timeString = time.strftime("%Y-%m-%d-%H-%M")
os.system("mv status.xml " + timeString + "-status.xml")
os.system("rm *csv")
os.system("rm *tmp")
