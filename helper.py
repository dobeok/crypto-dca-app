import pandas as pd

from pandas_datareader import data as pdr
import yfinance as yfin

import plotly.graph_objects as go

import time
import glob

# fetch_all_tickers
# fetch_ticker
# load_local_data
# simulate

yfin.pdr_override()


TICKER_DATA = {
    # crypto
    'BTC': 'BTC-USD',
    'ETH': 'ETH-USD',
    'AVAX': 'AVAX-USD',
    'BNB': 'BNB-USD',
    'XRP': 'XRP-USD',
    'ADA': 'ADA-USD',
    'SOL': 'SOL-USD',
    'DOGE': 'DOGE-USD',
    'DOT': 'DOT-USD',
    'MATIC': 'MATIC-USD',
    'UNI': 'UNI1-USD',
    'LINK': 'LINK-USD',
    
    # stocks
    'S&P 500': '^GSPC',
}


def fetch_all_tickers(ticker_dict=TICKER_DATA):
    """
    fetch latest data from yahoo finance and save to ./data/sample/
    """
    data = {}

    for ticker_name in ticker_dict.keys():
        try:
            data[ticker_name] = pdr.get_data_yahoo(ticker_dict[ticker_name])
            time.sleep(1)
        except Exception as e:
            print(f'Error fetching {ticker_name}\n{e}')
            pass


    for key, _ in data.items():
        print(f'saving {key} data')
        
        if len(data[key]):
            first = data[key].index.min().strftime('%Y-%m-%d')
            last = data[key].index.max().strftime('%Y-%m-%d')

            
            data[key].to_csv(f'./data/sample/{key} {first} {last}.csv')
            print(f'Updated {key} from {first} to {last}')


def fetch_ticker(ticker_name):
    """
    ticker_name needs to follow yahoo finance's symbols
    eg. TSLA, AAPL
    """
    try:
        df = pdr.get_data_yahoo(ticker_name)
        first = df.index.min().strftime('%Y-%m-%d')
        last = df.index.max().strftime('%Y-%m-%d')
        df.to_csv(f'./data/sample/{ticker_name} {first} {last}.csv')
    except:
        print(f'Unable to fetch data for ticker {ticker_name}')
        pass


def load_local_data(_coin_name='BTC', ticker_data=TICKER_DATA):
    file_names = glob.glob(f'data/sample/{_coin_name}*')
    if len(file_names):
        _df = pd.read_csv(max(file_names))
        _df.columns = _df.columns.str.lower()
    else:
        _df = pd.DataFrame()
        print('No local data available. Please try to fetch data from yahoo')
    
    return _df


def preprocess_time(_df, start_date=None):
    _df['date'] = pd.to_datetime(_df['date'])

    _df['week_no'] = _df['date'].dt.to_period('W')
    _df['month_no'] = _df['date'].dt.to_period('M')
    _df['quarter_no'] = _df['date'].dt.to_period('Q')

    
    if start_date is not None:
        start_date = start_date.strftime('%Y-%m-%d')
        _df = _df[_df['date']>=start_date]
    
    return _df


def get_frequency(_df, freq='weekly'):
    """
    create a frequency column to help identify entry points
    """
    freq = freq.lower()
    if freq == 'weekly':
        _df = _df.loc[_df['date'].isin(_df.groupby('week_no')['date'].min())][['week_no', 'high']].copy(deep=True)
    elif freq == 'monthly':
        _df = _df.loc[_df['date'].isin(_df.groupby('month_no')['date'].min())][['month_no', 'high']].copy(deep=True)
    elif freq == 'quarterly':
        _df = _df.loc[_df['date'].isin(_df.groupby('quarter_no')['date'].min())][['quarter_no', 'high']].copy(deep=True)
    

    # convert to str due to Arrow issues
    for col in ['week_no', 'month_no', 'quarter_no']:
        if col in _df.columns:
            _df[col] = _df[col].astype(str)
        
    if 'week_no' in _df.columns:
        _df['week_no'] = _df['week_no'].str[:10]

    return _df


def calculate_pnl(_df, _amount=100):
	_df['period_cost'] = _amount
	_df['cumulative_cost'] = _df['period_cost'].cumsum()
	_df['num_coins_bought'] = _df['period_cost'] / _df['high']
	_df['cumulative_coins_bought'] = _df['num_coins_bought'].cumsum()

	_df['portfolio_worth ($)'] = _df['cumulative_coins_bought'] * _df['high'] - _df['cumulative_cost']
	
	return _df


def init_plot():
    fig = go.Figure()
    fig.update_layout(
        yaxis_title="Portfolio worth ($)",
        
    )
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black')

    return fig


def plot_data(df, fig, name=None):
    """
    modify input df to create simplified axis names
    and add optional helpers for nicer plots
    TODO: add buy & hold option for comparison
    """

    chart_data = df.iloc[:, [0, 6]]
    chart_data.columns = [' '.join([word.capitalize() for word in token]) for token in [_.split('_') for _ in chart_data.columns]]

    # graph object
    
    fig.add_trace(go.Scatter(
        x=chart_data[chart_data.columns[0]],
        y=chart_data[chart_data.columns[1]],
        name=name,
        mode="lines",
        showlegend=True
    ))


def simulate_dca(coin_name, start_date, frequency, amount):
    df = load_local_data(coin_name)
    
    if len(df):
        df = preprocess_time(df, start_date)
        df = get_frequency(df, frequency)
        df = calculate_pnl(df, amount)
        df = df.reset_index(drop=True)
        
        return df

    # return empty dataframe
    return pd.DataFrame()


def calculate_metrics(coin_name, df):
    cumulative_pnl = df['portfolio_worth ($)'].round().to_list()[-1]
    num_coins_bought = df['cumulative_coins_bought'].round(2).to_list()[-1]
    total_usd_invested = df['cumulative_cost'].round(2).to_list()[-1]
    max_gains = df['portfolio_worth ($)'].max()
    max_losses = df['portfolio_worth ($)'].min()

    result = {
        'cumulative_pnl': cumulative_pnl,
        'num_coins_bought': num_coins_bought,
        'total_usd_invested': total_usd_invested,
        'max_gains': max_gains,
        'max_losses': max_losses
    }

    return {coin_name: result}


if __name__ == '__main__':
    fetch_all_tickers()