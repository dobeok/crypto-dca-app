import streamlit as st
import pandas as pd
from helper import simulate_dca, init_plot, plot_data, calculate_metrics, TICKER_DATA


st.set_page_config(
     page_title='DCA simulator',
     layout='wide',
     initial_sidebar_state='expanded',
)


@st.cache
def convert_df(_df):
   return _df.to_csv().encode('utf-8')


st.title('DCA simulator')

st.write("""
Dollar cost averaging (DCA) is an investment strategy where an investor regularly invests a fixed amount of money into a particular security, regardless of the current price.
Over time, the average cost per unit of the security is reduced as more shares are purchased at lower prices and fewer shares are purchased at higher prices.
This strategy is used to mitigate the impact of market volatility and reduce the average cost of investment over time.
""")

st.session_state.sample_data_disabled = False
st.session_state.sample_data_visibility = 'visible'

st.session_state.upload_data_disabled = True
st.session_state.sample_data_visibility = 'visible'


# sidebar
with st.sidebar:
    st.markdown('## 1. Select assets')
    st.session_state.var_all_coins_names = st.multiselect(
        label='select coins',
        default=['BTC', 'ETH'],
        options=TICKER_DATA.keys()
    )
    
    st.markdown('## 2. Select frequency and investment amount')

    st.number_input(
        'Amount to invest ($): ',
        value=100,
        min_value=0,
        step=50,
        key='var_amount',
        )
    
    
    frequency_list = ['Weekly', 'Monthly', 'Quarterly']
    st.radio(
        'Frequency: ',
        options=frequency_list,
        key='var_frequency',
        help=f'simulate buying at the beginning of the selected period',
    )

    
    default_start_date = pd.to_datetime("2020-01-01", format="%Y-%m-%d")
    st.date_input(
        'Start date: ',
        value=default_start_date,
        min_value=None,
        max_value=None,
        key='var_start_date',
    )

    
    st.checkbox('Compare againts S&P500', value=True, key='compare_SPX', disabled=False)


# run simulation for all coins selected
all_dfs = {}
for coin_name in st.session_state.var_all_coins_names:
    all_dfs[coin_name] = simulate_dca(
        coin_name,
        st.session_state.var_start_date,
        st.session_state.var_frequency,
        st.session_state.var_amount
        )

    all_dfs[coin_name]['coin'] = coin_name


all_summary = {}
for coin_name in st.session_state.var_all_coins_names:
    all_summary.update(calculate_metrics(coin_name, all_dfs[coin_name]))


# run simulation for SPX to benchmark (optional)
st.session_state.df_spx = simulate_dca(
    'S&P 500',
    st.session_state.var_start_date,
    st.session_state.var_frequency,
    st.session_state.var_amount
    )


st.markdown(f"""
---
### Results\n
Current strategy: Investing **${st.session_state.var_amount}** every **{st.session_state.var_frequency.lower()[:-2]}** into **{", ".join(st.session_state.var_all_coins_names)}**. Starting from **{st.session_state.var_start_date.strftime('%d %b %Y')}**
""")


fig = init_plot()
for _coin_name, _df in all_dfs.items():
    plot_data(
        _df,
        fig,
        _coin_name,
    )

if st.session_state.compare_SPX:
    plot_data(st.session_state.df_spx, fig, 'S&P 500')


st.plotly_chart(fig, use_container_width=True)


# summary table
st.dataframe(
    pd.DataFrame(all_summary).T.style.format("{:.2f}"),
    )


# download button
df_all_details = pd.concat(all_dfs.values())
st.download_button(
   "Download all data as csv",
   convert_df(df_all_details),
   f"sim {st.session_state.var_frequency} {st.session_state.var_amount}.csv",
   "text/csv",
   key='download-csv-all'
)


st.markdown("""
---\n###  Notes
1. Historical price data from [yahoo finance](https://sg.finance.yahoo.com/cryptocurrencies/)
2. Assuming both buy and sell prices are at intraday high
""")