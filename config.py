import os

from dotenv import load_dotenv

load_dotenv()

RPC_URL: str = "https://rpc.ankr.com/http/aptos/v1"
MIN_SWAP_PERCENT_BALANCE = 0.1
MAX_SWAP_PERCENT_BALANCE = 0.2

ACCOUNT_ADDRESS = os.getenv("ACCOUNT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
