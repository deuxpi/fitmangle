import fitparse
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import numpy as np
from scipy import signal
import seaborn as sns

import sys


sns.set(color_codes=True)


def main(filename):
    fitfile = fitparse.FitFile(
        filename,
        data_processor=fitparse.StandardUnitsDataProcessor(),
        check_crc=False)
    records = fitfile.get_messages('record')
    data = []
    fields = None
    trimp = 0.0
    for i, record in enumerate(records):
        speed = record.get('speed').value
        heart_rate = record.get('heart_rate').value
        y = (heart_rate - 60.0) / (185 - 60)
        trimp += (y / 60.0) * 0.64 * np.exp(1.92 * y)
        efficiency = 100000.0 * speed / 60.0 / heart_rate
        data.append([f.value for f in record.fields] + [efficiency])
        if fields is None:
            fields = [(f.name, f.units) for f in record.fields]
    fields.append(('Economy', 'cm/beat'))
    data = np.array(data)
    timestamps = data[10:, 0]
    data = signal.convolve(
        np.pad(
            data[10:, 1:], [(2, 2), (0, 0)],
            mode='median',
            stat_length=((10, 10), (0, 0))),
        [[0.2]] * 5,
        mode='valid')

    print 'TRIMP: {}'.format(trimp)

    ignored_fields = [
        'position_long', 'position_lat', 'timestamp', 'distance', 'cadence',
        'altitude', 'fractional_cadence',
        'enhanced_speed', 'enhanced_altitude']

    fig = plt.figure(figsize=(40, 30))
    fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)

    fignum = 1
    for i, (field_name, units) in enumerate(fields):
        if field_name in ignored_fields:
            continue
        series = data[:, i - 1]
        plt.subplot(4, 3, fignum)
        if field_name == 'speed':
            label = 'Pace'
            units = 'min/km'
        else:
            label = field_name.replace('_', ' ').capitalize()
        plt.plot(timestamps, series, label=label)
        if field_name == 'heart_rate':
            avg_heart_rate = int(np.median(series))
            max_heart_rate = int(max(series))
            avg_heart_rate_reserve = int(
                100.0 * (avg_heart_rate - 60.0) / (185.0 - 60.0))
            plt.axhline(y=avg_heart_rate, linestyle='--')
            plt.text(
                timestamps[0], avg_heart_rate,
                '{:d} ({:d}%)'.format(avg_heart_rate, avg_heart_rate_reserve),
                verticalalignment='bottom')
            plt.axhline(y=max_heart_rate, linestyle='--')
            plt.text(
                timestamps[0], max_heart_rate,
                '{:d}'.format(max_heart_rate),
                verticalalignment='bottom')
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
            plt.ylim((0.0, 1.5 * np.percentile(series, 90)))
        plt.ylabel(units)
        plt.legend()
        plt.grid(True)
        fignum += 1

    plt.show()


if __name__ == '__main__':
    main(sys.argv[1])
