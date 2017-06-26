import fitparse
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import numpy as np
import pandas as pd
import seaborn as sns

import sys


sns.set(color_codes=True)


class PaceFormatter(Formatter):
    def __call__(self, x, pos=None):
        if x == 0:
            pace = 0
        else:
            pace = 3600.0 / x
        return '{}:{:02d}'.format(int(pace / 60), int(pace % 60))


def plot_fitfile(filename):
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
            fields = [
                f.name.replace('_', ' ').capitalize()
                for f in record.fields] + ['Economy']
            units = {name: f.units for name, f in zip(fields, record.fields)}
            units['Economy'] = 'cm/beat'
    data = np.array(data)
    timestamps = data[10:, 0].astype('datetime64[ms]')
    timestamps = (timestamps - timestamps[0]).astype(float) / 60000.0
    if False:
        data = np.convolve(
            np.pad(
                data[10:, 1:], [(2, 2), (0, 0)],
                mode='median',
                stat_length=((10, 10), (0, 0))),
            [[0.2]] * 5,
            mode='valid')
    else:
        data = data[10:, 1:]

    print 'TRIMP: {}'.format(trimp)

    df = pd.DataFrame(data, columns=fields[1:], index=timestamps)

    ignored_fields = [
        'Position long', 'Position lat', 'Timestamp', 'Distance', 'Cadence',
        'Elevation', 'Altitude', 'Fractional cadence',
        'Enhanced speed', 'Enhanced altitude']
    for column in ignored_fields:
        try:
            del df[column]
        except KeyError:
            pass

    intervals = [30, 60, 300, 1800, 3600]
    peak_speed = []
    series = df['Speed']
    for interval in intervals:
        w = np.ones(interval, dtype=float)
        w /= w.sum()
        peak_speed.append(max(np.convolve(w, series, mode='valid')))
        peak_pace = 3600.0 / peak_speed[-1]
        print '{}:{:02d} {}:{:02d}'.format(
            interval / 60, interval % 60,
            int(peak_pace / 60), int(peak_pace % 60))
    plt.subplot(3, 3, 1)
    plt.semilogx(intervals, peak_speed, label='Peak pace')
    plt.ylabel('min/km')
    plt.gca().xaxis.set_ticks(intervals)
    plt.gca().xaxis.set_ticklabels(
        ["{}:{:02d}".format(i / 60, i % 60) for i in intervals])
    plt.gca().yaxis.set_major_formatter(PaceFormatter())
    plt.gca().yaxis.set_minor_formatter(PaceFormatter())
    plt.legend()

    fignum = 2
    for field_name in df.columns:
        plt.subplot(3, 3, fignum)
        df[field_name].plot()

        if field_name == 'Heart rate':
            series = df['Heart rate']
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
        if field_name == 'Speed':
            plt.gca().yaxis.set_major_formatter(PaceFormatter())
            plt.gca().yaxis.set_minor_formatter(PaceFormatter())

        plt.xlabel('Time')
        plt.ylim((0.0, 1.5 * np.percentile(df[field_name], 90)))
        plt.ylabel(units[field_name])
        plt.title(field_name)

        fignum += 1


if __name__ == '__main__':
    fig = plt.figure(figsize=(40, 30))
    fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)

    for filename in sys.argv[1:]:
        plot_fitfile(filename)

    plt.show()
