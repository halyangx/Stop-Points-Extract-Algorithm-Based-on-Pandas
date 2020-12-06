from abc import ABC

import pandas as pd
from ..preprocessing import filtering

SHIP_ID = 'uid'
TIMESTAMP = 'timestamp'
LONGITUDE = 'longitude'
LATITUDE = 'latitude'
ESSENTIAL_COLUMNS = [LONGITUDE, LATITUDE, TIMESTAMP, SHIP_ID]


class AisDataFrame(pd.DataFrame, ABC):

    def __init__(self, data, longitude=LONGITUDE, latitude=LATITUDE, timestamp=TIMESTAMP, ship_id=SHIP_ID):

        if isinstance(data, pd.DataFrame):
            adf = data.rename(columns=
                              {longitude: LONGITUDE,
                               latitude: LATITUDE,
                               timestamp: TIMESTAMP,
                               ship_id: SHIP_ID}
                              )
        else:
            raise TypeError('DataFrame constructor called with incompatible data and dtype: {e}'.format(e=type(data)))

        self._validate(adf)
        super().__init__(data=adf, columns=adf.columns)

    def _validate(self):
        if not set(ESSENTIAL_COLUMNS).issubset(self.columns):
            raise AttributeError("Must have 'longitude', 'latitude', 'timestamp', 'uid' columns")

    def _sort_values_by_uid_and_timestamp(self):
        return self.sort_values(by=[SHIP_ID, TIMESTAMP])

