import csv
import sys

from dateutil.parser import parse
from dateutil.tz import tzfile, tzutc

tz = [tzfile('/etc/localtime')]

print('date,weightkg')

with open(sys.argv[1]) as fitnotes_file:
    fitnotes_reader = csv.DictReader(fitnotes_file)
    for row in fitnotes_reader:
        date = parse('{} {}'.format(row['Date'], row['Time']), tzinfos=tz)
        print(','.join([
            date.astimezone(tzutc()).isoformat(),
            str(float(row['Value']) / 2.2046226),
        ]))
