import numpy as np
import pandas as pd

x_known = [0, 2, 4, 5, 7, 10, 11, 15, 17, 21, 27.5, 31, 31]  # rssi
y_known = [6.9, 6, 5, 4.5, 4, 3.25, 3, 2.38, 2, 1.5, 1, 0.5, 0]  # meters


def get_rssi_to_meters():
    x = np.arange(0, 32)
    y = np.interp(x, x_known, y_known)

    return dict(zip(x, y))


_rssi_to_meters_dict = get_rssi_to_meters()


def rssi_to_meters(v):
    return _rssi_to_meters_dict.get(v)


# Timestamp will be regenerated to miliseconds since begging of experiment
def regenerate_timestamp(df):
    grouped = df.groupby(['estimated_x', 'estimated_y'], sort=False)

    return pd.concat(
        df.assign(timestamp=(i+1)*500)
        for i, (_, df) in enumerate(grouped)
    )


def preprocess_dataset(dataframe):
    df = dataframe.drop(['estimated_x', 'estimated_y'], axis=1)
    df['distance'] = df['rssi'].apply(rssi_to_meters)

    df = regenerate_timestamp(df)

    return df
