import os
import sqlalchemy
import requests
import pandas as pd
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
    r = requests.get(os.environ['FLIPSIDE_API_ENDPOINT'], timeout=300)
    items = r.json()
    df = pd.DataFrame(items)
    df = df.drop_duplicates(subset=['TX_HASH','BLOCK_NUMBER'], keep='first')
    return df

def write_trades(df, engine):
    # check if tx_hash already exists
    existing_tx_hashes = existing_tx_hashes = pd.read_sql_query('select distinct("TX_HASH") from sudoswap_trades',engine)
    df = df[~df['TX_HASH'].isin(existing_tx_hashes['TX_HASH'].values.tolist())]
    df.to_sql('sudoswap_trades', engine, if_exists='append')