import asyncio
import random

from aptos_sdk.account import Account
from loguru import logger

import config
from contracts.base import TokenBase
from swap import LiquidSwapCurve


async def main():
    coin_x = TokenBase('aptos', '0x1::aptos_coin::AptosCoin')
    coin_y = TokenBase('usdc', '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC')
    account = Account.load_key(config.PRIVATE_KEY)
    module = LiquidSwapCurve(account, config.RPC_URL, coin_x=coin_x, coin_y=coin_y)
    await module.async_init()

    logger.success('coin_x: {} initial balance: {}', coin_x.symbol, module.initial_balance_x_wei)
    logger.success('coin_x: {} decimals: {}', coin_x.symbol, module.token_x_decimals)

    logger.success('coin_y: {} initial balance: {}', coin_y.symbol, module.initial_balance_y_wei)
    logger.success('coin_y: {} decimals: {}', coin_y.symbol, module.token_y_decimals)

    min_amount_out = module.initial_balance_x_wei * config.MIN_SWAP_PERCENT_BALANCE
    max_amount_out = module.initial_balance_x_wei * config.MAX_SWAP_PERCENT_BALANCE
    amount_out = round(random.uniform(min_amount_out, max_amount_out))
    logger.info('amount_out {}', amount_out)

    amount_in = await module.get_most_profitable_amount_in_and_set_pool_type(
        amount_out,
        coin_x.contract_address,
        coin_y.contract_address,
        module.token_x_decimals,
        module.token_y_decimals,
    )
    logger.success('amount_in: {}, selected pool: {}', amount_in, module.pool_type)


if __name__ == '__main__':
    asyncio.run(main())

