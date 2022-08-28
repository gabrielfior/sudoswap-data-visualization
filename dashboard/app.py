import streamlit as st
st.set_page_config(layout="wide", page_title='Sudoswap dashboard', initial_sidebar_state='expanded')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlalchemy
from plot_utils import *
import os
import dotenv
from io import BytesIO
import pathlib
dotenv.load_dotenv(pathlib.Path(__file__).parent.parent.joinpath('.env'))


st.title('Sudoswap dashboard')

tab1, tab2 = st.tabs(["Temporal evolution", "Wash trading"])

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

@st.experimental_memo(ttl=300)
def get_nftbank_data():
    df = pd.read_sql_query('''
    select *
    from nftbank_data;
    ''', engine)
    return df.drop(columns=['index'])

@st.experimental_memo(ttl=300)
def get_nftbank_stats():
    df = pd.read_sql_query('''
    select *
    from nftbank_stats;
    ''', engine)
    return df.drop(columns=['index'])

trades_by_date = get_num_trades()
nftbank_df = get_nftbank_data()
nftbank_stats = get_nftbank_stats()
tab1.bar_chart(trades_by_date, x='date', y='num_trades')

trades_nft = get_trades()
project_ref = pd.Series(trades_nft.project_name.values,index=trades_nft.nft_address).to_dict()

known_projects = ['0x1d20a51f088492a0f1c57f047a9e30c9ab5c07ea','0x026224a2940bfe258d0dbe947919b62fe321f042',
'0xe4cfae3aa41115cb94cff39bb5dbae8bd0ea9d41','0xca21d4228cdcc68d4e23807e5e370c07577dd152']
options = st.sidebar.multiselect(
     'NFT Address',
     default=known_projects,
     options = list(sorted(project_ref.keys())),
     format_func=lambda x: f"Collection - {project_ref.get(x, 'NO NAME')}")


filtered_trades_nft = trades_nft[(trades_nft['nft_address'].isin(options)) & (~trades_nft.price_usd.isna())].sort_values(
    'block_timestamp', ascending=True)
filtered_trades_nft.index = pd.to_datetime(filtered_trades_nft['block_timestamp'])

### plot trades on sudoswap
fig1, ax1 = plot_trades_nft(filtered_trades_nft)
tab1.pyplot(fig1)

def show_metric(stats, key, label):
    metric = stats.get(key)
    tab1.metric(label, "${:,.2f}".format(metric) if metric is not None else "")

tab1.markdown(get_divider_html(), unsafe_allow_html=True)

if options:
    for nft_address in options:
        
        stats_df = nftbank_stats[nftbank_stats.nft_address==nft_address]
        floor_estimated_df = nftbank_df[nftbank_df.nft_address==nft_address]
        
        if not stats_df.empty:
            stats = stats_df.iloc[0]
            tab1.subheader(f'Collection: {project_ref.get(nft_address, "NONE")} | Address: {nft_address}')
            cols = st.columns(4)
            with cols[0]:
                show_metric(stats, 'floor_price_usd', 'Floor price')
            with cols[1]:
                show_metric(stats, 'pastmonth_average_usd', 'Past month average floor price')
            with cols[2]:
                show_metric(stats, 'pastmonth_trade_volume_usd', 'Past month trade volume')
            with cols[3]:
                show_metric(stats, 'total_trade_volume_usd', 'Total trade volume')
            
        with tab1.container():
            if not floor_estimated_df.empty:
                fig2, ax2 = plt.subplots(figsize=(8,4))
                floor_estimated_df['processedAt'] = pd.to_datetime(floor_estimated_df['processedAt'])
                cols = [i for i in floor_estimated_df.columns if i != 'processedAt']
                floor_estimated_df.plot(x = 'processedAt', y=cols,ax=ax2)
                ax2.xaxis.set_major_locator(plt.MaxNLocator(7))
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))

                ax2.set_xlabel('Datetime')
                ax2.set_ylabel('Price ETH')
                ax2.set_title('Estimated & Floor prices')
                ax2.grid(True)
                fig2.autofmt_xdate()
                
                buf = BytesIO()
                fig2.savefig(buf, format="png")
                tab1.image(buf)
                            

tab1.markdown(get_divider_html(), unsafe_allow_html=True)

if not options:
    tab2.subheader('Select options on the dropdown')
else:

    expander = tab2.expander("See washtrading calculation methodology", expanded=False)
    expander.write("""
    The basic idea of wash trading is that one trader is trading the same NFT using two distinct wallets, thus making it seems like there is more trading activity for a given NFT than there actually is. Those trades also occur within a short time difference of each other. For our example, we consider a trade of type "wash trade" when two addresses trade the same NFT address back-and-forth (i.e. 2 trades) within a 1h period.
    """)

    
    fig3,ax3, plot_df = plot_washtrading(trades_nft, project_ref, options)
    tab2.dataframe(plot_df.rename(columns={'wash_trade':'num_wash_trades'}))
    tab2.pyplot(fig3)
    