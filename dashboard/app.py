import streamlit as st
import pandas as pd
import numpy as np
import sqlalchemy
import os
import dotenv
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

trades_by_date = get_num_trades()
st.bar_chart(trades_by_date, x='date',y='num_trades')