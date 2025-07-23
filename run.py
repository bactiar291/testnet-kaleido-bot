import os
import time
import json
import platform
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

os.system('cls' if platform.system() == 'Windows' else 'clear')

RPC_URL = "https://api.testnet.abs.xyz"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS = web3.to_checksum_address(os.getenv("WALLET_ADDRESS"))

FAUCET_CONTRACT = web3.to_checksum_address("0xC99eddf1f7C9250728A47978732928aE158396E7")
USDC_SELECTOR = "0x4451d89f"
KLD_SELECTOR = "0x45d3b1f7"

USDC_ADDRESS = web3.to_checksum_address("0x572f4901f03055ffC1D936a60Ccc3CbF13911BE3")
DESTINATION = web3.to_checksum_address("0x2aC60481a9EA2e67D80CdfBF587c63c88A5874ac")
AMOUNT_WEI = 1000
CHAIN_ID = 11124

ERC20_ABI = json.loads('[{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
DEST_ABI = json.loads('[{"constant":false,"inputs":[{"name":"token","type":"address"},{"name":"amount","type":"uint256"}],"name":"depositCollateral","outputs":[],"type":"function"}]')

def get_last_claim_time(selector):
    print(f"\U0001F50E Mengecek klaim {selector} ...")
    try:
        latest = web3.eth.block_number
        logs = web3.eth.get_logs({
            "fromBlock": latest - 5000,
            "toBlock": "latest",
            "address": FAUCET_CONTRACT,
            "topics": [selector]
        })
        for log in reversed(logs):
            if log['address'].lower() == FAUCET_CONTRACT.lower() and WALLET_ADDRESS.lower() in log['topics'][1].hex().lower():
                return log['blockNumber']
    except Exception as e:
        print(f"Gagal cek log: {e}")
    return None

def can_claim_again(last_block):
    if last_block is None:
        return True, 0
    current = web3.eth.block_number
    blocks_left = 420 - (current - last_block)
    if blocks_left <= 0:
        return True, 0
    return False, blocks_left * 10 // 7  

def send_raw_tx(contract, func, args):
    try:
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)
        tx = contract.functions[func](*args).build_transaction({
            'from': WALLET_ADDRESS,
            'gas': 800000,
            'gasPrice': web3.to_wei('0.1', 'gwei'),
            'nonce': nonce,
            'chainId': CHAIN_ID
        })
        signed = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"TX terkirim: {web3.to_hex(tx_hash)}")
        web3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Gagal kirim TX: {e}")

def auto_claim(selector, label):
    last_block = get_last_claim_time(selector)
    bisa, tunggu = can_claim_again(last_block)
    if bisa:
        print(f"\u2705 Mengklaim {label}...")
        try:
            tx = {
                'to': FAUCET_CONTRACT,
                'from': WALLET_ADDRESS,
                'data': selector,
                'gas': 150000,
                'gasPrice': web3.to_wei('0.1', 'gwei'),
                'nonce': web3.eth.get_transaction_count(WALLET_ADDRESS),
                'chainId': CHAIN_ID
            }
            signed = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"✅ Klaim {label} TX: {web3.to_hex(tx_hash)}")
        except Exception as e:
            print(f"Gagal klaim {label}: {e}")
    else:
        print(f"⏳ {label} belum bisa diklaim. Tunggu ~{tunggu} detik lagi")

def menu_claim():
    mode = input("Mode klaim (1 = Sekali, 2 = Terus Menerus): ").strip()
    while mode not in ["1", "2"]:
        mode = input("Input salah. Pilih 1 atau 2: ").strip()
    while True:
        auto_claim(USDC_SELECTOR, "USDC")
        auto_claim(KLD_SELECTOR, "KLD")
        if mode == "1":
            break
        print("⏲️ Menunggu 70 menit untuk klaim berikutnya...")
        time.sleep(70 * 60)

def menu_deposit():
    try:
        count = int(input("Berapa kali ingin melakukan transaksi? ").strip())
        if count <= 0:
            raise ValueError
    except:
        print("Input tidak valid. Harus angka positif.")
        return

    token_contract = web3.eth.contract(address=USDC_ADDRESS, abi=ERC20_ABI)
    dest_contract = web3.eth.contract(address=DESTINATION, abi=DEST_ABI)

    print("\nStep 1: Approve USDC...")
    send_raw_tx(token_contract, 'approve', [DESTINATION, 2**256 - 1])

    print("\nStep 2: Deposit USDC sebanyak", count, "kali...")
    for i in range(count):
        print(f"\n⛏️ Deposit ke-{i+1}...")
        send_raw_tx(dest_contract, 'depositCollateral', [USDC_ADDRESS, AMOUNT_WEI])


def main():
    print("""
===================================================
     🚀 BOT ABSTRACT TESTNET | BACTIAR291 
===================================================
1) Auto-Claim Faucet (USDC & KLD)
2) Approve & Deposit Collateral
0) Keluar
""")
    pilihan = input("Pilih opsi (1/2/0): ").strip()
    if pilihan == "1":
        menu_claim()
    elif pilihan == "2":
        menu_deposit()
    elif pilihan == "0":
        print("Sampai jumpa!")
    else:
        print("Input tidak valid.")

if __name__ == "__main__":
    main()
