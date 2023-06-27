from loguru import logger
from os import getcwd
from json import load
from web3 import Web3, AsyncHTTPProvider
from web3.eth import AsyncEth
from random import choice, randint
import asyncio, aiohttp
import csv
import requests
from time import sleep

path = getcwd()
CONNECTED_RPCS = {}
DELAY = 0.1



with open(f"wallets.txt", "r") as f:
    WALLETS = [row.strip() for row in f]


with open(f"{path}\\Scripts\\erc20.json", "r", encoding='utf-8') as f:
    ERC20_ABI = load(f)

with open(f"{path}\\Scripts\\stg.json", "r", encoding='utf-8') as f:
    STG = load(f)


TOKENS = {
    "USDT": {
        "ETH": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "BSC": "0x55d398326f99059fF775485246999027B3197955",
        "MATIC": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "ARB": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "AVAX": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
    },
    "USDC": {
        "ETH": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "BSC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "FTM": "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75",
        "MATIC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "ARB": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "AVAX": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        "ZKSYNC": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
        "OP": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607"
    },
    "BTCB": {
        "BSC": "0x2297aEbD383787A160DD0d9F71508148769342E3",
        "MATIC": "0x2297aEbD383787A160DD0d9F71508148769342E3",
        "ARB": "0x2297aEbD383787A160DD0d9F71508148769342E3",
        "AVAX": "0x152b9d0FdC40C096757F570A51E494bd4b943E50"
    },
    "STG": {
        "MATIC" : "0x3AB2DA31bBD886A7eDF68a6b60D3CDe657D3A15D",
        "ARB"   : "0xfBd849E6007f9BC3CC2D6Eb159c045B8dc660268",
        "BSC"   : "0xD4888870C8686c748232719051b677791dBDa26D",
        "AVAX"  : "0xCa0F57D295bbcE554DA2c07b005b7d6565a58fCE",
        "FTM"   : "0x933421675cDC8c280e5F21f0e061E77849293dba"
    }
}

RPC = {
    "ETH": ["http://136.243.59.93:8545"],
    "BSC": ["http://167.235.180.166:8545"],
    "FTM": ["http://167.235.180.166:9545"],
    "MATIC": ["http://148.251.126.86:8545"],
    "ARB": ["http://136.243.59.93:8547"],
    "AVAX": ["http://148.251.126.86:9650/ext/bc/2q9e4r6Mu3U68nU1fYjgbR6JvwrRx36CohpAX5UQxse55x1Q5/rpc"],
    "GOERLY": ["https://eth-goerli.public.blastapi.io"],
    "ZKSYNC": ["https://mainnet.era.zksync.io"],
    "OP": ["http://148.251.126.86:9991"]
}

SUPPORTED_TICKERS = ["ETHUSDT", "BNBUSDT", "FTMUSDT", "MATICUSDT", "ARBUSDT", "AVAXUSDT", "BTCUSDT", "STGUSDT"]

ether_fields = [f"{net}_N" for net in RPC.keys()]
usdt_fields = [f"{net}_USDT" for net in TOKENS["USDT"].keys()]
usdc_fields = [f"{net}_USDC" for net in TOKENS["USDC"].keys()]
btcb_fields = [f"{net}_BTCB" for net in TOKENS["BTCB"].keys()]
stg_fields  = [f"{net}_STG" for net in TOKENS["STG"].keys()]
other_fields = ["ADDRESS", "USD_BALANCE"]

FIELDS = [usdc_fields, usdt_fields, btcb_fields, ether_fields, other_fields, stg_fields]
