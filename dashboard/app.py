import streamlit as st
st.set_page_config(layout="wide")
from fetch_nftbank import NftBankAdapter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlalchemy
import os
import dotenv
from io import BytesIO
import pathlib
dotenv.load_dotenv(pathlib.Path(__file__).parent.parent.joinpath('.env'))


st.title('Sudoswap dashboard')

@st.experimental_singleton
def get_engine():
    user = os.environ['DB_USERNAME']
    pw = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOST'] 
    db_url = f'postgresql://{user}:{pw}@{host}:5432'
    engine = sqlalchemy.create_engine(db_url)
    return engine

engine = get_engine()


@st.experimental_memo(ttl=300)
def get_num_trades():
    trades_by_date = pd.read_sql_query('''
    select DATE("block_timestamp") as date, count(*) as num_trades
from sudoswap_trades
group by DATE("block_timestamp")
order by DATE("block_timestamp") DESC;
    ''', engine)
    return trades_by_date


@st.experimental_memo(ttl=300)
def get_trades():
    trades_of_nft = pd.read_sql_table('sudoswap_trades', engine)
    trades_of_nft.replace('null', None, inplace=True)
    trades_of_nft['price_usd'] = pd.to_numeric(trades_of_nft['price_usd'])
    trades_of_nft['block_timestamp'] = pd.to_datetime(trades_of_nft['block_timestamp'])
    return trades_of_nft


# bar chart
# ToDo - Include volume
trades_by_date = get_num_trades()
st.bar_chart(trades_by_date, x='date', y='num_trades')

trades_nft = get_trades()


project_ref = pd.Series(trades_nft.project_name.values,index=trades_nft.nft_address).to_dict()

options = st.sidebar.multiselect(
     'NFT Address',
     options = list(project_ref.keys()),
     format_func=lambda x: f"Collection - {project_ref.get(x, 'NO NAME')}")

#option = st.selectbox("Select option", options=list(CHOICES.keys()), format_func=format_func)

filtered_trades_nft = trades_nft[(trades_nft['nft_address'].isin(options)) & (~trades_nft.price_usd.isna())].sort_values(
    'block_timestamp', ascending=True)
filtered_trades_nft.index = pd.to_datetime(filtered_trades_nft['block_timestamp'])
#st.dataframe(trades_nft[trades_nft['NFT_ADDRESS'].isin(options)])

fig = plt.figure()
ax = fig.add_subplot(111)

filtered_trades_nft.groupby('nft_address')['price_usd'].plot(ax=ax)

ax.xaxis.set_major_locator(plt.MaxNLocator(7))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %M %Y'))
#ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

plt.xlabel('Transaction datetime')
plt.ylabel('Price USD')
plt.title('Executed trades on sudoswap')
ax.grid(True)
fig.autofmt_xdate()

plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

st.pyplot(fig)

nft_bank_adapter = NftBankAdapter()

if options:
    for nft_address in options:
        
        stats = nft_bank_adapter.get_nft_statistics(nft_address)
        
        if stats is not None and stats != []:
            st.subheader(f'Collection: {project_ref.get(nft_address, "NONE")} | Address: {nft_address}')
            cols = st.columns(4)
            with cols[0]:
                st.metric('Floor price', "${:,.2f}".format(stats.get('floor_price_usd', "")))
            with cols[1]:
                st.metric('Past month average floor price', "${:,.2f}".format(stats.get('pastmonth_average_usd', "")))
            with cols[2]:
                st.metric('Past month trade volume', "${:,.2f}".format(stats.get('pastmonth_trade_volume_usd', "")))
            with cols[3]:
                st.metric('Total trade volume', "${:,.2f}".format(stats.get('total_trade_volume_usd', "")))


# ToDo - Add NFT estimated price (as bar chart) - in USD
# use https://docs.nftbank.ai/nft-valuation-api/historical-valuation-api/v3-estimated-price for each NFT
# plot line chart
