import streamlit as st
import pandas as pd
from millify import millify
from helper import update_data, simulate, init_plot, plot_data, calculate_metrics, TICKER_DATA
import glob


st.set_page_config(
     page_title="Crypto DCA app",
     layout="wide",
     initial_sidebar_state="expanded",
)


@st.cache
def convert_df(_df):
   return _df.to_csv().encode('utf-8')


st.title('Crypto DCA app')
st.markdown('Dollar cost averaging (DCA) is investing a fixed amount of money into a particular investment at regular intervals, typically monthly or quarterly.')


with st.expander("Read more.."):
    st.markdown("""
    * This strategy is simple to understand, but retail investors often find it hard to excute due to them being susceptible to emotional investing.
    
    * 2 most common mistakes are FOMO - overbuy then market rallies, or staying out completely when market dips and waiting for market to recover.
        - when market tops, the same dollar amount could buy fewer underlying assets
        - in contrast, it is virtually impossible to time the market bottom. So by staying out during downturns, investors miss out on the chance to buy cheaply

    * Hence, DCA is often a good strategy for the unsophisicated investors.
    """)


with st.sidebar:
    st.selectbox('Pick your asset: ', key='var_coin_name', options=list(TICKER_DATA.keys()))
    st.number_input('Amount to invest ($): ', value=100,  min_value=0, step=50, key='var_amount')
    
    frequency_list = ['Weekly', 'Monthly', 'Quarterly', 'Yearly']
    st.radio('Frequency: ', options=frequency_list, key='var_frequency', help=f'simulate buying {st.session_state.var_coin_name} at the beginning of the selected period')

    default_start_date = pd.to_datetime("2019-01-01", format="%Y-%m-%d")
    st.date_input('Start date: ', value=default_start_date, min_value=None, max_value=None, key='var_start_date')

    
    st.checkbox('Compare againts S&P500', key='compare_SPX', disabled=False)
    # st.checkbox('Compare againts lump sum investment', key='compare_ls', disabled=True)
    st.markdown("---")
    st.session_state.file_names = glob.glob(f'./data/{st.session_state.var_coin_name}*')
    if len(st.session_state.file_names):
        st.session_state.latest_date = max(st.session_state.file_names)[-14:-4]
        st.write(f'Latest data for {st.session_state.var_coin_name}: {st.session_state.latest_date}')
    st.button(label='Update data', on_click=update_data)

st.session_state.df = simulate(
    st.session_state.var_coin_name,
    st.session_state.var_start_date,
    st.session_state.var_frequency,
    st.session_state.var_amount
    )

st.session_state.df_spx = simulate(
    'S&P 500',
    st.session_state.var_start_date,
    st.session_state.var_frequency,
    st.session_state.var_amount
    )


st.markdown(f"""### Results\n
Current strategy: Investing **${st.session_state.var_amount}** every **{st.session_state.var_frequency.lower()[:-2]}** into **{st.session_state.var_coin_name}**, starting from **{st.session_state.var_start_date.strftime('%d %b %Y')}**
""")


# chart
fig = init_plot()
plot_data(st.session_state.df, fig, st.session_state.var_coin_name)

if st.session_state.compare_SPX:
    plot_data(st.session_state.df_spx, fig, 'S&P 500')

st.plotly_chart(fig, use_container_width=True)


# summary metrics
col1, col2, col3, col4, col5 = st.columns(5)

(st.session_state.cumulative_pnl, st.session_state.num_coins_bought,
st.session_state.total_usd_invested, st.session_state.max_gains,
st.session_state.max_losses) = calculate_metrics(st.session_state.df)

col1.metric(label='PnL to-date', value=f"${millify(st.session_state.cumulative_pnl)}")
col2.metric(label=f'# {st.session_state.var_coin_name} bought', value=st.session_state.num_coins_bought)
col3.metric(label='Total invested', value=f"${millify(st.session_state.total_usd_invested)}")
col4.metric(label='Max gains', value=f"${millify(st.session_state.max_gains)}")
col5.metric(label='Max losses', value=f"${millify(st.session_state.max_losses)}")


# st.dataframe(st.session_state.df)


st.download_button(
   "Download data as csv",
   convert_df(st.session_state.df),
   f"{st.session_state.var_coin_name} {st.session_state.var_frequency} {st.session_state.var_amount}.csv",
   "text/csv",
   key='download-csv'
)


st.markdown("""
---\n###  Notes

1. Historical price data from [yahoo finance](https://sg.finance.yahoo.com/cryptocurrencies/)
2. Assuming buy at intraday low and sell at intraday high
3. This is a personal project and **not financial advice**. I am not responsible for the accuracy and integrity of the data. Please do your own research!

""")