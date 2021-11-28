import logging
from datetime import datetime

import pandas as pd

from .bar import Bar


class Bars:
    """Pricing and financial data for given Symbol.

    The OHLCV, and if available, dividends, stock splits for a given
    financial instrument. Price change, dividend yield and return
    are calculated if appropriate.

    Parameters
    ----------


    Attributes
    ----------

    Methods
    -------

    """

    def __init__(self, df, source, asset, raw=None):
        """
        df columns: open, high, low, close, volume, dividend, stock_splits
        df index: pd.Timestamp localized at the timezone America/New_York
        """
        if df.shape[0] == 0:
            raise NoBarDataFound(source, asset)
        self.df = df
        self.source = source.upper()
        self.asset = asset
        self.symbol = asset.symbol.upper()
        self._raw = raw

    def __repr__(self):
        return repr(self.df)

    def _repr_html_(self):
        return self.df._repr_html_()

    @classmethod
    def parse_bar_list(cls, bar_list, source, asset):
        raw = []
        for bar in bar_list:
            raw.append(bar)

        df = pd.DataFrame(raw)
        df = df.set_index("timestamp")
        df["price_change"] = df["close"].pct_change()
        df["dividend_yield"] = df["dividend"] / df["close"]
        df["return"] = df["dividend_yield"] + df["price_change"]
        bars = cls(df, source, asset, raw=bar_list)
        return bars

    def split(self):
        """Return a list of Bars objects, each with a single bar

        Parameters
        ----------
        None

        Returns
        -------
        list of Bars objects
        """
        result = []
        for index, row in self.df.iterrows():
            item = {
                "timestamp": int(index.timestamp()),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "dividend": row.get("dividend", 0),
                "stock_splits": row.get("stock_splits", 0),
            }
            bar = Bar(item)
            result.append(bar)

        return result

    def get_last_price(self):
        """Return the last price of the last bar

        Parameters
        ----------
        None

        Returns
        -------
        float

        """
        return self.df["close"][-1]

    def get_last_dividend(self):
        """Return the last dividend of the last bar

        Parameters
        ----------
        None

        Returns
        -------
        float
        """
        if "dividend" in self.df.columns:
            return self.df["dividend"][-1]
        else:
            logging.warning("Unable to find 'dividend' column in bars")
            return 0

    def filter(self, start=None, end=None):
        """Return a Bars object with only the bars between start and end

        Parameters
        ----------
        start : datetime.datetime
            The start of the range to filter on

        end : datetime.datetime
            The end of the range to filter on

        Returns
        -------
        Bars object
        """
        df_copy = self.df
        if isinstance(start, datetime):
            df_copy = df_copy[df_copy.index >= start]
        if isinstance(end, datetime):
            df_copy = df_copy[df_copy.index <= end]

        return df_copy

    def get_momentum(self, start=None, end=None):
        """Return the momentum (return based on closing prices) of the bars between start and end

        Parameters
        ----------
        start : datetime.datetime
            The start of the range to filter on (inclusive) (default: None)

        end : datetime.datetime
            The end of the range to filter on (inclusive) (default: None)

        Returns
        -------
        float
        """
        df_copy = self.filter(start=start, end=end)
        n_rows = df_copy.shape[0]
        if n_rows == 0:
            return 0

        momentum = df_copy["close"].pct_change(n_rows - 1)[-1]
        return momentum

    def get_total_volume(self, start=None, end=None):
        """Return the total volume of the bars between start and end

        Parameters
        ----------
        start : datetime.datetime
            The start of the range to filter on (inclusive) (default: None)

        end : datetime.datetime
            The end of the range to filter on (inclusive) (default: None)

        Returns
        -------
        float
        """
        df_copy = self.filter(start=start, end=end)
        n_rows = df_copy.shape[0]
        if n_rows == 0:
            return 0

        volume = df_copy["volume"].sum()
        return volume

    def aggregate_bars(self, frequency):
        """
        Will convert a set of bars to a different timeframe (eg. 1 min to 15 min)
        frequency (string): The new timeframe that the bars should be in, eg. "15Min", "1H", or "1D"
        Returns a new bars object.

        Parameters
        ----------
        frequency : str
            The new timeframe that the bars should be in, eg. "15Min", "1H", or "1D"

        Returns
        -------
        Bars object

        Examples
        --------
        >>> # Get the 15 minute bars for the last hour
        >>> bars = self.get_symbol_bars("AAPL", 60, "minute")
        >>> bars_agg = bars.aggregate_bars("15Min")
        """
        new_df = self.df.groupby(pd.Grouper(freq=frequency)).agg(
            {
                "open": "first",
                "close": "last",
                "low": "min",
                "high": "max",
                "volume": "sum",
            }
        )
        new_df.columns = ["open", "close", "low", "high", "volume"]
        new_df = new_df.dropna()

        new_bars = Bars(new_df, self.source, self.asset)

        return new_bars


class NoBarDataFound(Exception):
    def __init__(self, source, asset):
        message = (
            f"{source} did not return data for symbol {asset}. "
            f"Make sure there is no symbol typo or use another data source"
        )
        super(NoBarDataFound, self).__init__(message)

    def aggregate_bars(self, frequency):
        """
        Will convert a set of bars to a different timeframe (eg. 1 min to 15 min)
        frequency (string): The new timeframe that the bars should be in, eg. "15Min", "1H", or "1D"
        Returns a new bars object.
        """
        new_df = self.df.groupby(pd.Grouper(freq=frequency)).agg(
            {
                "open": "first",
                "close": "last",
                "low": "min",
                "high": "max",
                "volume": "sum",
            }
        )
        new_df.columns = ["open", "close", "low", "high", "volume"]
        new_df = new_df.dropna()

        new_bars = Bars(new_df, self.source, self.asset)

        return new_bars


class NoBarDataFound(Exception):
    def __init__(self, source, asset):
        message = (
            f"{source} did not return data for symbol {asset}. "
            f"Make sure there is no symbol typo or use another data source"
        )
        super(NoBarDataFound, self).__init__(message)
