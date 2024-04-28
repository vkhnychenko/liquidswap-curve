import os
import sys

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", '1') in ['1', 'true']

logger.remove()
if DEBUG_MODE:
    logger.add(sys.stderr, level="DEBUG")
else:
    logger.add(sys.stderr, level="INFO")


RPC_URL: str = "https://rpc.ankr.com/http/aptos/v1"
MIN_SWAP_PERCENT_BALANCE = 0.1
MAX_SWAP_PERCENT_BALANCE = 0.2

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
