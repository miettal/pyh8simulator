import sys,os
sys.path.append(os.pardir)
from simpleh8simulator import *

sim = SimpleH8simulator()

sim.load("sample.mot")
sim.reset()

while True :
  sim.runStep()
  if len(sim.outputBuf) > 0 :
    sys.stdout.write("%c" % sim.outputBuf.pop())
