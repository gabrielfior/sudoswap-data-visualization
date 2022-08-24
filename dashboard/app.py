import streamlit as st
st.set_page_config(layout="wide")
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
    select DATE("BLOCK_TIMESTAMP") as date, count(*) as num_trades
from sudoswap_trades
group by DATE("BLOCK_TIMESTAMP")
order by DATE("BLOCK_TIMESTAMP") DESC;
    ''', engine)
    return trades_by_date


@st.experimental_memo(ttl=300)
def get_trades():
    trades_of_nft = pd.read_sql_query('''
    select *
    from sudoswap_trades;
    ''', engine)
    trades_of_nft.replace('null', None, inplace=True)
    trades_of_nft['PRICE_USD'] = pd.to_numeric(trades_of_nft['PRICE_USD'])
    trades_of_nft['BLOCK_TIMESTAMP'] = pd.to_datetime(trades_of_nft['BLOCK_TIMESTAMP'])
    return trades_of_nft


# bar chart
# ToDo - Include volume
trades_by_date = get_num_trades()
st.bar_chart(trades_by_date, x='date', y='num_trades')

trades_nft = get_trades()


options = st.multiselect(
     'NFT Address',
     trades_nft['NFT_ADDRESS'].unique().tolist())

filtered_trades_nft = trades_nft[(trades_nft['NFT_ADDRESS'].isin(options)) & (~trades_nft.PRICE_USD.isna())].sort_values(
    'BLOCK_TIMESTAMP', ascending=True)
filtered_trades_nft.index = pd.to_datetime(filtered_trades_nft['BLOCK_TIMESTAMP'])
#st.dataframe(trades_nft[trades_nft['NFT_ADDRESS'].isin(options)])

fig = plt.figure()
ax = fig.add_subplot(111)

filtered_trades_nft.groupby('NFT_ADDRESS')['PRICE_USD'].plot(ax=ax)

ax.xaxis.set_major_locator(plt.MaxNLocator(7))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
#ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %M %Y'))
#ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')

plt.xlabel('Transaction datetime')
plt.ylabel('Price USD')
ax.grid(True)
fig.autofmt_xdate()

plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

st.pyplot(fig)