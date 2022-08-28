import schedule
import time
from job_definition import *
from loguru import logger
logger.add("job_flipside_{time}.log", rotation="500 MB")

def job():
    engine = get_engine()
    logger.info("Fetching data")
    df = fetch_data_flipside()

    nft_addresses = df['nft_address'].unique().tolist()
    df_nftbank = fetch_data_nftbank(nft_addresses)
    df_nftbank_stats = fetch_metadata_nft(nft_addresses)

    logger.info("Writing trades")
    write_trades(df, engine)
    logger.info("Writing nftbank data")
    write_nftbank_data(df_nftbank, engine)
    write_nftbank_stats(df_nftbank_stats, engine)
    logger.info("Finished")

schedule.every(2).hours.at(":30").do(job)

while True:
    schedule.run_pending()
    time.sleep(120)
    logger.info("Sleeping...")