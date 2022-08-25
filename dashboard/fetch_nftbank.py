from email import header
import requests
import os

class NftBankAdapter:
    def __init__(self) -> None:
        self.api_key = os.environ['NFTBANK_API_KEY']
    
    def get_nft_statistics(self, nft_address):
        headers = {"x-api-key": self.api_key}
        url = f"https://api.nftbank.ai/estimates-v2/collections/{nft_address}?chain_id=ETHEREUM"
        r = requests.get(url, headers=headers)
        return r.json()['data']