import fitparse
import matplotlib.pyplot as plt
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
        data.append([f.value for f in record.fields])
        if fields is None:
            fields = [f.name for f in record.fields]
    data = np.array(data)

    ignored_fields = [
        'position_long', 'position_lat', 'timestamp', 'distance',
        'fractional_cadence', 'enhanced_speed',
        'enhanced_altitude']

    fig = 1
    for i, field in enumerate(fields):
        if field in ignored_fields:
            continue
        plt.figure(fig)
        if field == 'speed':
            series = 60.0 / (data[:, i] + 0.1)
            label = 'Pace'
        else:
            label = field.replace('_', ' ').capitalize()
            series = data[:, i]
        plt.plot(series, label=label)
        plt.ylim((0.0, 1.5 * np.percentile(series, 80)))
        plt.legend()
        fig += 1

    plt.show()


if __name__ == '__main__':
    main(sys.argv[1])
