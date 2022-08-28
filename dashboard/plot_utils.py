import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import seaborn as sns

def plot_trades_nft(trades_nft_df):
    fig, ax = plt.subplots()
    trades_nft_df.groupby('nft_address')['price_usd'].plot(ax=ax)

    ax.xaxis.set_major_locator(plt.MaxNLocator(7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))

    ax.set_xlabel('Transaction datetime')
    ax.set_ylabel('Price USD')
    ax.set_title('Executed trades on sudoswap')
    ax.grid(True)
    fig.autofmt_xdate()
    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

    return fig,ax

def plot_washtrading(trades_nft, project_ref, nft_addresses_to_filter):
    trades_temp = trades_nft
    trades_temp['pairings'] = trades_temp.apply(lambda x: order_addresses(x['buyer_address'],x['seller_address']),axis=1)
    trades_temp['block_timestamp_day'] = trades_temp['block_timestamp'].dt.date
    trades_temp.sort_values(['block_timestamp','pairings'], inplace=True)
        
    trades_temp['rank'] = trades_temp.groupby(['nft_address','block_timestamp_day','seller_address','buyer_address']).cumcount()
    trades_temp = trades_temp.sort_values(['rank'])

    diff_df = trades_temp.groupby(['rank','nft_address','pairings','block_timestamp_day'],as_index=False).agg(
        {'block_timestamp': lambda x: x.diff().dropna()})

    diff_df['signal'] = diff_df['block_timestamp'].apply(create_signal_from_grouped_transactions)
    diff_df = diff_df[diff_df['signal']!=False]
    diff_df = diff_df.explode('block_timestamp')
    diff_df['wash_trade'] = diff_df['block_timestamp'].apply(lambda x: abs(x) <= datetime.timedelta(hours=1))
    plot_df = diff_df[(diff_df['wash_trade']) & 
                            (diff_df['nft_address'].isin(nft_addresses_to_filter))].groupby(
                                ['nft_address','block_timestamp_day'],as_index=False)['wash_trade'].count()

    
    plot_df['project_name'] = plot_df['nft_address'].apply(lambda x: project_ref.get(x))
    

    fig, ax = plt.subplots(figsize=(8,4))
    sns.lineplot(x="block_timestamp_day", y="wash_trade", hue="nft_address", data=plot_df, ax=ax)
    #plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    ax.set_title('Wash trading over time')
    ax.set_xlabel('Block timestamp')
    ax.set_ylabel('# of wash trades')

    ax.xaxis.set_major_locator(plt.MaxNLocator(7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))

    ax.grid(True)
    fig.autofmt_xdate()
    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")


    return fig,ax,plot_df
    


def get_divider_html():
    return '<hr style="border: 0;border-top: 2px dashed brown;">'

def order_addresses(ad1,ad2):
    first = ad1 if ad1>ad2 else ad2
    second = ad2 if ad1>ad2 else ad1
    return '{}-{}'.format(first,second)

def create_signal_from_grouped_transactions(x):
    try:
        return False if x.size ==0 else True
    except:
        return None