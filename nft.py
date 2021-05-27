from stat_ import *

def get_nft(account):
    #table_name = convert_account(account)
    url = f"https://wax.api.atomicassets.io/atomicassets/v1/assets?owner={account}&page=1&limit=100000&order=desc&sort=asset_id"
    out = requests.get(url)
    out = json.loads(out.text)
    out = out['data']
    print(len(out))
    nfts = []
    for i in range(len(out) - 1):
        nfts.append(out[i]['name'])
    return nfts
