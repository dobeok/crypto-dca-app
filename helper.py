from pandas_datareader import data
import plotly.graph_objects as go
import pandas as pd
import time
import glob


SOURCE = 'yahoo'
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


def update_data(ticker_data=TICKER_DATA, source=SOURCE):
    """
    update all tickers at once, then save to csv in ./data
    """
    for name, ticker in ticker_data.items():
        try:
            _df = data.DataReader(ticker, source)
            _df = _df.reset_index()
            _df.columns = _df.columns.str.lower()
        
        
            time.sleep(1)

            if len(_df):
                # save data and print out latest entry's date
                _latest_date = _df['date'].max().strftime('%Y-%m-%d')
                _df.to_csv(f'./data/{name} {_latest_date}.csv')
                print(f'updated {name} to {_latest_date}')
            
        except Exception as e:
            print(e)


def load_local_data(_coin_name='BTC', ticker_data=TICKER_DATA):
    file_names = glob.glob(f'data/{_coin_name}*')
    if len(file_names):
        _df = pd.read_csv(max(file_names))
    else:
        _df = pd.DataFrame()
    
    return _df


def preprocess_time(_df, start_date=None):
    _df['date'] = pd.to_datetime(_df['date'])

    _df['week_no'] = _df['date'].dt.to_period('W')
    _df['month_no'] = _df['date'].dt.to_period('M')
    _df['quarter_no'] = _df['date'].dt.to_period('Q')
    _df['year_no'] = _df['date'].dt.to_period('Y')

    
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
    elif freq == 'yearly':
        _df = _df.loc[_df['date'].isin(_df.groupby('year_no')['date'].min())][['year_no', 'high']].copy(deep=True)

    # convert to str due to Arrow issues
    for col in ['week_no', 'month_no', 'quarter_no', 'year_no']:
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
        mode="markers+lines",
        showlegend=True
    ))


def simulate(coin_name, start_date, frequency, amount):
    df = load_local_data(coin_name)
    df = preprocess_time(df, start_date)
    df = get_frequency(df, frequency)
    df = calculate_pnl(df, amount)
    df = df.reset_index(drop=True)

    return df


def calculate_metrics(df):
    cumulative_pnl = df['portfolio_worth ($)'].round().to_list()[-1]
    num_coins_bought = df['cumulative_coins_bought'].round(2).to_list()[-1]
    total_usd_invested = df['cumulative_cost'].round(2).to_list()[-1]
    max_gains = df['portfolio_worth ($)'].max()
    max_losses = df['portfolio_worth ($)'].min()
    
    return cumulative_pnl, num_coins_bought, total_usd_invested, max_gains, max_losses


if __name__ == '__main__':
    update_data()