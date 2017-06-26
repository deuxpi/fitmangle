import fitparse
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import numpy as np
import pandas as pd
import seaborn as sns

import sys


sns.set(color_codes=True)


class MinutesFormatter(Formatter):
    def __call__(self, x, pos=None):
        if x > 3600:
            h = '{}:'.format(int(x / 3600))
            x %= 3600
        else:
            h = ''
        return '{}{}:{:02d}'.format(h, int(x / 60), int(x % 60))


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
    values = []
    fields = None
    for record in fitfile.get_messages('record'):
        values.append([f.value for f in record.fields])
        if fields is None:
            fields = [
                f.name.replace('_', ' ').capitalize()
                for f in record.fields]
            units = {name: f.units for name, f in zip(fields, record.fields)}

    df = pd.DataFrame(values, columns=fields)
    df.set_index('Timestamp')

    ignored_fields = [
        'Position long', 'Position lat', 'Timestamp', 'Distance', 'Cadence',
        'Elevation', 'Altitude', 'Fractional cadence',
        'Enhanced speed', 'Enhanced altitude']
    for column in ignored_fields:
        try:
            del df[column]
        except KeyError:
            pass

    df['Economy'] = 100000.0 * df['Speed'] / 60.0 / df['Heart rate']
    units['Economy'] = 'cm/beat'

    y = (df['Heart rate'] - 60.0) / (185.0 - 60.0)
    trimp = ((y / 60.0) * 0.64 * np.exp(y.astype(float) * 1.92)).sum()
    print 'TRIMP: {}'.format(trimp)

    intervals = [30, 60, 300, 1800, 3600]
    peak_speed = []
    series = df['Speed']
    for interval in intervals:
        w = np.ones(interval, dtype=float)
        w /= w.sum()
        peak_speed.append(max(np.convolve(w, series, mode='valid')))
    plt.subplot(3, 3, 1)
    plt.semilogx(intervals, peak_speed)
    plt.ylabel('min/km')
    plt.gca().xaxis.set_ticks(intervals)
    plt.gca().xaxis.set_ticklabels(
        ["{}:{:02d}".format(i / 60, i % 60) for i in intervals])
    plt.gca().yaxis.set_major_formatter(PaceFormatter())
    plt.gca().yaxis.set_minor_formatter(PaceFormatter())
    plt.title('Peak pace')

    fignum = 2
    for field_name in df.columns:
        plt.subplot(3, 3, fignum)
        ax = df[field_name].plot()

        if field_name == 'Heart rate':
            series = df['Heart rate']
            avg_heart_rate = int(np.median(series))
            max_heart_rate = int(max(series))
            avg_heart_rate_reserve = int(
                100.0 * (avg_heart_rate - 60.0) / (185.0 - 60.0))

            color = ax.get_lines()[-1].get_color()
            plt.axhline(y=avg_heart_rate, linestyle='--', color=color)
            plt.text(
                0, avg_heart_rate,
                '{:d} ({:d}%)'.format(avg_heart_rate, avg_heart_rate_reserve),
                verticalalignment='bottom')
            plt.axhline(y=max_heart_rate, linestyle='--', color=color)
            plt.text(
                0, max_heart_rate,
                '{:d}'.format(max_heart_rate),
                verticalalignment='bottom')

        plt.xlabel('Time')
        plt.gca().xaxis.set_major_formatter(MinutesFormatter())
        plt.gca().xaxis.set_minor_formatter(MinutesFormatter())
        plt.ylim((0.0, 1.5 * np.percentile(df[field_name], 90)))
        plt.ylabel(units[field_name])

        if field_name == 'Speed':
            plt.gca().yaxis.set_major_formatter(PaceFormatter())
            plt.gca().yaxis.set_minor_formatter(PaceFormatter())
            plt.title('Pace')
        else:
            plt.title(field_name)

        fignum += 1


if __name__ == '__main__':
    fig = plt.figure(figsize=(40, 30))
    fig.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)

    for filename in sys.argv[1:]:
        plot_fitfile(filename)

    plt.show()
