import fitparse
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import numpy as np

import sys


def main(filename):
    fitfile = fitparse.FitFile(
        filename,
        data_processor=fitparse.StandardUnitsDataProcessor(),
        check_crc=False)
    records = fitfile.get_messages('record')
    data = []
    fields = None
    for i, record in enumerate(records):
        speed = record.get('speed').value
        heart_rate = record.get('heart_rate').value
        efficiency = 100000.0 * speed / 60.0 / heart_rate
        data.append([f.value for f in record.fields] + [efficiency])
        if fields is None:
            fields = [(f.name, f.units) for f in record.fields]
    fields.append(('Economy', 'cm/beat'))
    data = np.array(data)

    ignored_fields = [
        'position_long', 'position_lat', 'timestamp', 'distance',
        'fractional_cadence', 'enhanced_speed', 'enhanced_altitude']

    fignum = 1
    for i, (field_name, units) in enumerate(fields):
        if field_name in ignored_fields:
            continue
        plt.subplot(4, 3, fignum)
        timestamps = data[:, 0]
        if field_name == 'speed':
            label = 'Pace'
            units = 'min/km'
        else:
            label = field_name.replace('_', ' ').capitalize()
        plt.plot(timestamps, data[:, i], label=label)
        if field_name == 'speed':
            class MinutesFormatter(Formatter):
                def __call__(self, x, pos=None):
                    if x == 0:
                        pace = 0
                    else:
                        pace = 3600.0 / x
                    return '{}:{:02d}'.format(int(pace / 60), int(pace % 60))

            plt.gca().yaxis.set_major_formatter(MinutesFormatter())
            plt.gca().yaxis.set_minor_formatter(MinutesFormatter())
        elif field_name == 'altitude' or field_name == 'Elevation':
            plt.ylim((-100.0, 100.0))
        else:
            plt.ylim((0.0, 1.5 * np.percentile(data[:, i], 80)))
        plt.ylabel(units)
        plt.legend()
        plt.grid(True)
        fignum += 1

    plt.show()


if __name__ == '__main__':
    main(sys.argv[1])
