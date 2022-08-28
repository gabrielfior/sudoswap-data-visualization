import datetime
import json
import os
import sqlalchemy
import requests
import pandas as pd
from shroomdk import ShroomDK
from alive_progress import alive_bar
from loguru import logger

import dotenv
dotenv.load_dotenv('../.env')


def get_engine():
    user = os.environ['DB_USERNAME']
    pw = os.environ['DB_PASSWORD']
    host = os.environ['DB_HOST'] 
    db_url = f'postgresql://{user}:{pw}@{host}:5432'
    engine = sqlalchemy.create_engine(db_url)
    return engine

def fetch_data_flipside():

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

def fetch_metadata_nft(nft_addresses):

    total_df = pd.DataFrame(data={}, columns=['processedAt','floorPriceEth','estimatedPriceEth', 'nft_address'])
    headers = {"Content-Type":"application/json", "x-api-key": os.environ['NFTBANK_API_KEY']}

    specified_cols = ['floor_price_usd', 'pastmonth_average_usd', 'pastmonth_trade_volume_usd', 'total_trade_volume_usd',
    'nft_address']
    total_df = pd.DataFrame(data={}, columns=specified_cols)

    with alive_bar(len(nft_addresses)) as bar:
        for nft_address in nft_addresses:         
            # ToDo
            url = f"https://api.nftbank.ai/estimates-v2/collections/{nft_address}?chain_id=ETHEREUM"
            r = requests.get(url, headers=headers)
            temp_df = pd.DataFrame(r.json()['data'],index=[0])
            if not temp_df.empty:
                temp_df['nft_address'] = nft_address
                total_df = pd.concat([total_df, temp_df[specified_cols]])
            bar()

    return total_df

def fetch_data_nftbank(nft_addresses):

    total_df = pd.DataFrame(data={}, columns=['processedAt','floorPriceEth','estimatedPriceEth', 'nft_address'])
    headers = {"Content-Type":"application/json", "x-api-key": os.environ['NFTBANK_API_KEY']}

    with alive_bar(len(nft_addresses)) as bar:  
        for nft_address in nft_addresses:         
            # ToDo

            # estimated
            try:
                r = requests.get(f"https://api.nftbank.ai/v3/estimated-price/ethereum/{nft_address}/1", headers=headers)
                estimated_prices = pd.DataFrame(r.json()['data'])
            except Exception as e:
                logger.exception(f'Could not parse nft_address {nft_address} estimated prices')
                estimated_prices = pd.DataFrame()

            if not estimated_prices.empty:
                estimated_prices['estimatedPriceEth'] = pd.to_numeric(estimated_prices['estimatedPriceEth'])        

            # floor
            try:
                r = requests.get(f"https://api.nftbank.ai/v3/floor-price/ethereum/{nft_address}", headers=headers)
                floor_prices = pd.DataFrame(r.json()['data'])
            except Exception as e:
                logger.exception(f'Could not parse nft_address {nft_address} floor prices')
                floor_prices = pd.DataFrame()
            
            
            if not floor_prices.empty:
                floor_prices['floorPriceEth'] = pd.to_numeric(floor_prices['floorPriceEth'])
            
            if estimated_prices.empty and floor_prices.empty:
                temp_df = pd.DataFrame()
            elif estimated_prices.empty:
                temp_df = floor_prices
            elif floor_prices.empty:
                temp_df = estimated_prices
            else:
                temp_df = floor_prices.merge(estimated_prices, on='processedAt')
            
            if not temp_df.empty:
                temp_df['nft_address'] = nft_address
                total_df = pd.concat([total_df, temp_df])
            
            bar()

    return total_df
        

def write_trades(df, engine):
    # check if tx_hash already exists
    existing_tx_hashes = pd.read_sql_query('select distinct("tx_hash") from sudoswap_trades',engine)
    df = df[~df['tx_hash'].isin(existing_tx_hashes['tx_hash'].values.tolist())]
    df['token_metadata'] = df['token_metadata'].apply(json.dumps)
    df.to_sql('sudoswap_trades', engine, if_exists='append')

def write_nftbank_data(df, engine):
    df.to_sql('nftbank_data', engine, if_exists='replace')

def write_nftbank_stats(df, engine):
    df.to_sql('nftbank_stats', engine, if_exists='replace')