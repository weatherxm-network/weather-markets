import requests
from decision import decide
import os
import sys
from datetime import datetime, timezone, timedelta
from tqdm import tqdm
import json
from web3 import Web3

PINATA_JWT = os.getenv('PINATA_JWT')
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
BETTING_PLATFORM = os.getenv("BETTING_PLATFORM")
BET_NAME = os.getenv("BET_NAME")
GROUP_ID = os.getenv("GROUP_ID")

def get_unix_timestamp(date_str, date_format="%Y-%m-%d"):
    dt = datetime.strptime(date_str, date_format)
    return int(dt.replace(tzinfo=timezone.utc).timestamp())

def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def store_cid_on_chain(date, platform, bet_name, cid):
    with open("./abi/IPFSIndexer.json") as f:
        contract_abi = json.load(f)
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
    nonce = w3.eth.get_transaction_count(account.address)
    txn = contract.functions.storeCID(date, platform, bet_name, cid).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': w3.eth.gas_price
    })
    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"⏳ Waiting for transaction {tx_hash.hex()} to be mined...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # Extract details
    if receipt.status == 1:
        print(f"✅ CID stored on-chain successfully!")
        print(f"🔗 TX Hash: {tx_hash.hex()}")
        print(f"📦 Block Number: {receipt.blockNumber}")
        print(f"⛽ Gas Used: {receipt.gasUsed}")
    else:
        print(f"❌ Transaction failed! TX Hash: {tx_hash.hex()}")

def fetch_events(namespace, limit, basin_base_url, after, before):
    try:
        url = f"{basin_base_url}/{namespace}/events"
        params = {
            "limit": limit,
            "after": after-2,
            "before": before+2
        }
        print(params)
        response = requests.get(url, params=params)
        print(f"Response Status: {response.status_code}")
        events = response.json()
        response.raise_for_status()
        cids = [event['cid'] for event in events if 'cid' in event]
        return cids
    except Exception as e:
        print(f"ERROR FETCHING CID: {str(e)}")

def download_from_ipfs(cid, save_dir=".", gateway="http://localhost:8080/ipfs/"):
    """
    Download a file from IPFS locally.
    Args:
        cid (str): The IPFS Content Identifier (CID) of the file.
        save_dir: The directory where to save the fetched files from IPFS
        gateway (str): The IPFS gateway URL. Default is taken from environment variables.
    Returns:
        file_path: The file path where the file from IPFS is stored.
    """
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, cid)

    # If local node fails or not available, fallback to public IPFS gateway
    try:
        print(f"FALLBACK: FETCHING CID {cid} FROM IPFS GATEWAY")
        url = f"{gateway}/{cid}"
        response = requests.get(url,stream=True)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            print(f"DOWNLOADED FILE TO {file_path} FROM LOCAL IPFS GATEWAY.")
            return file_path
        else:
            print(f"FAILED TO DOWNLOAD {cid}. HTTP STATUS: {response.status_code}")
    except Exception as e:
        print(f"ERROR DOWNLOADING FROM IPFS GATEWAY: {str(e)}")
        

def download_from_basin(cid, save_dir="."):
    """
    Download a file from Basin using its CID and save it locally.
    Args:
        cid (str): The CID of the file to download.
        save_dir (str): The directory to save the downloaded file.
    Returns:
        str: The local file path where the file is saved.
    Raises:
        Exception: If the download fails.
    """
    base_url = f"https://basin.tableland.xyz/events/{cid}"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{cid}.parquet")
    try:
        print(f"DOWNLOADING CID {cid}")
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"FILE DOWNLOADED AND SAVED TO {file_path}")
        return file_path
    except requests.exceptions.RequestException as e:
        print(f"FAILED TO DOWNLOAD CID {cid}: {e}")
        raise Exception(f"ERROR DOWNLOADING FILE FROM BASIN: {e}")
    
def upload_json_and_pin(devices, date):
    if not PINATA_JWT:
        print("PINATA_JWT is not set. Skipping Pinata storage.")
        return
    try:
        json_str = json.dumps(devices)  
        files = {
            'file': ('data.json', json_str, 'application/json')
        }
        devLen = len(devices["devices"])
        data = {
            "network": "public",
            "name": f"{BET_NAME}_{date}.json",
            "group": GROUP_ID,
            "keyvalues": json.dumps({
                    "devicesNum": str(devLen),
                    "medianCelciusTemp": str(devices["median_temperature_celsius"]),
                    "medianFarenheitTemp": str(devices["median_temperature_fahrenheit"]),
                    "betName": BET_NAME,
                    "platform": BETTING_PLATFORM,
                    "date": date
            })
        }
        print(data)
        upload_url = "https://uploads.pinata.cloud/v3/files"
        headers = {
            "Authorization": f"Bearer {PINATA_JWT}"
        }
        upload_response = requests.post(upload_url, headers=headers, files=files, data=data)
        try:
            upload_response_json = upload_response.json()
        except json.JSONDecodeError:
            print("❌ ERROR: Failed to decode JSON response from Pinata. Raw response:")
            print(upload_response.text)  # Print the raw response to debug
            return

        if upload_response.status_code != 200:
            print("❌ FILE UPLOAD FAILED:", upload_response_json)
            return

        print("✅ UPLOAD RESPONSE:", json.dumps(upload_response_json, indent=4))

        file_data = upload_response_json.get("data")
        if not file_data:
            print("❌ ERROR: No 'data' field in response.")
            return

        file_id = file_data.get("id")

        if not file_id:
            print("❌ FAILED TO RETRIEVE FILE ID.")
            return
        group_url = f"https://api.pinata.cloud/v3/groups/public/{GROUP_ID}/ids/{file_id}"
        group_response = requests.put(group_url, headers=headers)
        try:
            group_response = group_response.json()
        except json.JSONDecodeError:
            print("❌ ERROR: Failed to decode JSON response from Pinata for adding file id to group. Raw response:")
            print(group_response.text)  # Print the raw response to debug
            return
        cid = file_data.get("cid")
        if cid:
            print(f"✅ Successfully uploaded & pinned. CID: {cid}")
        else:
            print("❌ ERROR: CID not found in response.")
        # Convert date to integer format YYYYMMDD
        date_object = datetime.strptime(date, "%Y-%m-%d")
        date_integer = int(date_object.strftime("%Y%m%d"))
        if PRIVATE_KEY:
            print(f"🟢 STORING CID {cid} ON-CHAIN FOR {date}")
            store_cid_on_chain(date_integer, BETTING_PLATFORM, BET_NAME, cid)
        else:
            print("⚠️ PRIVATE_KEY not found. Skipping smart contract interaction.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    namespace = os.getenv('BASIN_NAMESPACE')
    limit = 10

    date = os.getenv('DATE')
    date_object = datetime.strptime(date, '%Y-%m-%d')
    before_date = date_object + timedelta(days=2)
    basin_base_url = os.getenv('BASIN_API_BASE_URL')

    after = get_unix_timestamp(date)
    before = get_unix_timestamp(before_date.strftime("%Y-%m-%d"))
    gateway = os.getenv("IPFS_GATEWAY", "https://ipfs.io/ipfs")
    print(f"FETCHING CID FOR {date} ({date})")
    try:
        cids = fetch_events(namespace, limit, basin_base_url, after=after, before=before)
        if len(cids)>0:
            print(f"RETRIEVED CID: {cids[0]} FROM BASIN")
            print(f"\n PROCESSING CID {cids[0]}")
            path = download_from_basin(cids[0])
            print(f"\n FETCHED DATA FROM IPFS")
            decision,filtered_devices = decide(path, True)
            # print(decision,filtered_devices)
            # REMOVE FILE AFTER PROCESSING IT AND DOWNLOAD THE NEXT ONE
            os.remove(path)
            if type(decision) != str:  
                celsius_temp = round(float(decision), 2)
                fahrenheit_temp = celsius_to_fahrenheit(celsius_temp)
                devices_list = json.loads(filtered_devices)
                results = {
                    "date": date,
                    "devices": devices_list,
                    "median_temperature_celsius": celsius_temp,
                    "median_temperature_fahrenheit": fahrenheit_temp
                }
                output_filename = f"temperature_results_{date}.json"
                with open(output_filename, "w") as f:
                    json.dump(results, f, indent=4)
                print(f"SAVED RESULTS LOCALY AS {output_filename}")
                upload_json_and_pin(results, date)    
                print(f"MEDIAN HIGHEST TEMP FOR {date}: {round(float(decision),2)} °C is equal to {fahrenheit_temp}°F")
            else:
                print('NO DEVICES MEET THE CRITERIA TO CALCULATE MEDIAN HIGHEST TEMPERATURE')
        else:
            print(f"NO CIDs RETRIEVED FROM IPFS FOR {date}")
    except Exception as e:
        print(f"An error occurred: {e}")




