import pandas as pd
import numpy as np
import yfinance as yf
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt

# -------------------------------
# Data Loader
# -------------------------------
class DataLoader:
    def __init__(self, ticker, start, end):
        self.ticker = ticker
        self.start = start
        self.end = end

    def get_data(self):
        """Fetch OHLCV data from Yahoo Finance (or other source)."""
        data = yf.download(self.ticker, start=self.start, end=self.end)
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        return data


# -------------------------------
# Strategy Base Class
# -------------------------------
class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Given OHLCV data, return a signal Series (+1 long, -1 short, 0 hold)."""
        pass


# Example: Moving Average Crossover
class MovingAverageStrategy(Strategy):
    def __init__(self, short=20, long=50):
        self.short = short
        self.long = long

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return +1 when short MA crosses above long MA, -1 when below."""
        signals = pd.Series(0, index=data.index)
        short_ma = data['Close'].rolling(self.short).mean()
        long_ma = data['Close'].rolling(self.long).mean()

        signals[short_ma > long_ma] = 1
        signals[short_ma < long_ma] = -1
        return signals


# -------------------------------
# Backtest Engine
# -------------------------------
class BacktestEngine:
    def __init__(self, data: pd.DataFrame, strategies: list, capital=10000, fee=0.001):
        self.data = data
        self.strategies = strategies
        self.capital = capital
        self.fee = fee
        self.results = {}

    def run(self):
        """Run all strategies and store portfolio values."""
        for strat in self.strategies:
            signals = strat.generate_signals(self.data)
            portfolio = self.simulate_trades(signals)
            self.results[strat.__class__.__name__] = portfolio
        return self

    def simulate_trades(self, signals: pd.Series) -> pd.Series:
        """Given signals, simulate trades and return equity curve."""
        cash = self.capital
        position = 0
        equity_curve = []

        for date, signal in signals.items():
            price = self.data.loc[date, 'Close']

            # Simple rule: fully long or fully out
            if signal == 1 and position == 0:  # Buy
                position = cash / price * (1 - self.fee)
                cash = 0
            elif signal == -1 and position > 0:  # Sell
                cash = position * price * (1 - self.fee)
                position = 0

            # Track portfolio value
            total_value = cash + position * price
            equity_curve.append(total_value)

        return pd.Series(equity_curve, index=signals.index)

    def compare(self):
        """Print performance summary of all strategies."""
        for name, curve in self.results.items():
            total_return = (curve.iloc[-1] / curve.iloc[0]) - 1
            print(f"{name}: {total_return:.2%}")

    def plot_equity_curves(self):
        """Plot portfolio value over time for each strategy."""
        for name, curve in self.results.items():
            plt.plot(curve, label=name)
        plt.legend()
        plt.title("Equity Curves")
        plt.show()
