import schedule
import time
from job_definition import *
from loguru import logger
logger.add("job_flipside_{time}.log", rotation="500 MB")

def job():
    logger.info("Getting engine")
    engine = get_engine()
    logger.info("Fetching data")
    df = fetch_data()
    logger.info("Writing trades")
    write_trades(df, engine)
    logger.info("Finished")

schedule.every(2).hours.at(":30").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
    logger.info("Sleeping...")