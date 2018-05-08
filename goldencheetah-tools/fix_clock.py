import json
import sys

with open(sys.argv[1]) as f:
    record = json.loads(f.read().decode('utf-8-sig'))

ride = record['RIDE']

intervals = ride['INTERVALS']
for interval in intervals:
    if interval['START'] > 75000:
        interval['START'] -= 75075
    if interval['STOP'] > 75000:
        interval['STOP'] -= 75075

samples = ride['SAMPLES']
for sample in samples:
    if sample['SECS'] > 75000:
        sample['SECS'] -= 75075

samples = ride['XDATA'][0]['SAMPLES']
for sample in samples:
    if sample['SECS'] > 75000:
        sample['SECS'] -= 75075

with open('fixed.json', 'w') as f:
    json.dump(record, f, indent=4)
