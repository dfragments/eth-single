# -*- coding: utf-8 -*-
from web3 import Web3
import time
import random
import requests
from datetime import datetime, timedelta

# Connect to the Monad network via Infura RPC
infura_url = "https://testnet-rpc.monad.xyz"
web3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))

# Check if the connection is successful
if not web3.is_connected():
    raise Exception("Failed to connect to Monad network")

# Constants
CHAIN_ID = 10143  # Monad Chain ID
MAX_RETRIES = 3  # Maximum retries per transaction
PRIVATE_KEY = ""  # Hardcoded private key (replace with caution)
INTERVAL_MINUTES = 720  # Interval in minutes for automatic execution
PREVIOUS_CHOICE = None  # Store the previous choice

# Function to check wallet balance
def check_balance(address):
    balance_wei = web3.eth.get_balance(address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    return balance_eth

# Function to generate a random contract address
def generate_random_contract_address():
    return Web3.to_checksum_address("0x" + "".join(random.choices("0123456789abcdef", k=40)))

# Function to generate a random wallet address
def generate_random_wallet_address():
    random_address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return Web3.to_checksum_address(random_address)

# Function to send ETH transaction
def send_eth_transaction(private_key, repetitions, amount, to_contracts=True):
    sender_address = web3.eth.account.from_key(private_key).address
    value_to_send = web3.to_wei(amount, 'ether')

    for i in range(repetitions):
        to_address = generate_random_contract_address() if to_contracts else generate_random_wallet_address()

        for attempt in range(MAX_RETRIES):
            try:
                nonce = web3.eth.get_transaction_count(sender_address)
                gas_price = web3.eth.gas_price * 1.1
                estimated_gas_limit = web3.eth.estimate_gas({
                    'from': sender_address,
                    'to': to_address,
                    'value': value_to_send
                })
                gas_limit = int(estimated_gas_limit * 1.2)

                tx = {
                    'nonce': nonce,
                    'to': to_address,
                    'value': value_to_send,
                    'gas': gas_limit,
                    'gasPrice': int(gas_price),
                    'chainId': CHAIN_ID
                }

                signed_tx = web3.eth.account.sign_transaction(tx, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)  # Fix attribute name
                print(f"Transaction {i+1}/{repetitions} sent to {to_address} with {amount} ETH! Tx Hash: {web3.to_hex(tx_hash)}")
                break
            except requests.exceptions.HTTPError as e:
                print(f"HTTPError on attempt {attempt+1}: {e}")
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                else:
                    print("Transaction failed after maximum retries.")

        time.sleep(5)

    print("Daily transfer task completed!")

# Function to automate daily transfers
def automate_daily_transfers():
    global PREVIOUS_CHOICE
    sender_address = web3.eth.account.from_key(PRIVATE_KEY).address
    balance = check_balance(sender_address)
    print(f"Current balance: {balance} ETH")
    
    if balance < 0.0001:
        print("Insufficient balance. Skipping transfers.")
        return
    
    if PREVIOUS_CHOICE is None:
        print("Select the transaction type for today:")
        print("1: Send 0 ETH to contracts")
        print("2: Send 0.0001 ETH to wallets")
        PREVIOUS_CHOICE = input("Enter 1 or 2: ")
    else:
        print(f"Using previous choice: {PREVIOUS_CHOICE}")
    
    repetitions = 5  # Set how many times to perform transaction daily
    
    if PREVIOUS_CHOICE == "1":
        send_eth_transaction(PRIVATE_KEY, repetitions, 0, to_contracts=True)
    elif PREVIOUS_CHOICE == "2":
        send_eth_transaction(PRIVATE_KEY, repetitions, 0.0001, to_contracts=False)
    else:
        print("Invalid choice. Skipping today's transfer.")

# Initiate the first transaction immediately
automate_daily_transfers()

# Schedule the function to run at a set interval
next_run = datetime.now() + timedelta(minutes=INTERVAL_MINUTES)
while True:
    now = datetime.now()
    if now >= next_run:
        automate_daily_transfers()
        next_run = now + timedelta(minutes=INTERVAL_MINUTES)
    remaining_time = next_run - now
    print(f"Next transaction in: {remaining_time.seconds // 60} minutes and {remaining_time.seconds % 60} seconds", end="\r")
    time.sleep(1)  # Check every 1 second
