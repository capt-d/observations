import sys
from core import *


file_provided = False
args_count = len(sys.argv) 

if args_count == 1:
    print('No arguments provided')
    exit()
elif args_count > 2 :
    print('Provide one argument')
    exit()

raw_rows = []
notify_reciver = NotifyReciver('')
data_grabber = DataGrabber(notify_reciver)
data_checker = DataChecker(notify_reciver)
calculator = Calculator(notify_reciver)
data_saver = DataSaver(notify_reciver)
results = CalculationsResults()
try:
    raw_rows = data_grabber.getFromFile(sys.argv[1])
except OSError:
   notify_reciver('Can not open file')
   exit()

if not raw_rows:
    exit()
results.position = data_checker.checkPosition(raw_rows[0])
if not results.position:
    exit()
results.bodies = data_checker.checkData(raw_rows[1:])
raw_rows =[]
if not results.position or not results.bodies:
    exit()
eph  = load('de421.bsp')
results.bodies = data_checker.bodyData(results.bodies, eph)
if len(results.bodies) == 0:
    exit()
results.place = wgs84.latlon(results.position.latitude 
                                * eval(results.position.NS),
                                results.position.longitude 
                                * eval(results.position.WE)) 
results.earth = eph['earth']
results.pos_on_earth = results.earth + results.place
results.bodies = calculator.getRisesAndSets(results.bodies, eph, results.place)

results.bodies = calculator.calcRates(results.pos_on_earth, results.place, results.bodies)
data_saver.saveCSV(results.bodies)

exit()


