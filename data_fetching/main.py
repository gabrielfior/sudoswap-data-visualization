from job_definition import *
from loguru import logger
logger.add("job_flipside_{time}.log", rotation="500 MB")

if __name__ == "__main__":

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