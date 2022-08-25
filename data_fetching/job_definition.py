import datetime
import json
import os
import sqlalchemy
import requests
import pandas as pd
from shroomdk import ShroomDK

import dotenv
dotenv.load_dotenv('../.env')



def get_engine():
    user = os.environ['DB_USERNAME']
    pw = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOST'] 
    db_url = f'postgresql://{user}:{pw}@{host}:5432'
    engine = sqlalchemy.create_engine(db_url)
    return engine

def fetch_data():

    sdk = ShroomDK(os.environ['FLIPSIDE_API_KEY'])
    day_before_yesterday = datetime.datetime.now() - datetime.timedelta(days=2)
    sql = f"""
        select *
        from ethereum.core.ez_nft_sales
        where 1=1
        and platform_name = 'sudoswap'
        and block_timestamp >= '{day_before_yesterday.strftime('%Y-%m-%d %H:%M:%S')}'
        order by block_timestamp desc;
        """

    query_result_set = sdk.query(sql)
    df = pd.DataFrame(query_result_set.records)
    df = df.drop_duplicates(subset=['tx_hash','block_number'], keep='first')
    return df

def write_trades(df, engine):
    # check if tx_hash already exists
    existing_tx_hashes = pd.read_sql_query('select distinct("tx_hash") from sudoswap_trades',engine)
    df = df[~df['tx_hash'].isin(existing_tx_hashes['tx_hash'].values.tolist())]
    df['token_metadata'] = df['token_metadata'].apply(json.dumps)
    df.to_sql('sudoswap_trades', engine, if_exists='append')