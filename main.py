import asyncio
import random

from aptos_sdk.account import Account
from loguru import logger

import config
from contracts.base import TokenBase
from liquidswap.swap import LiquidSwapCurve

PAIRS = [
    (
        ('aptos', '0x1::aptos_coin::AptosCoin'),
        ('usdc', '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC')
    ),
    (
        ('aptos', '0x1::aptos_coin::AptosCoin'),
        ('stAPT', '0xd11107bdf0d6d7040c6c0bfbdecb6545191fdf13e8d8d259952f53e1713f61b5::staked_coin::StakedAptos')
    )
]


async def main():
    account = Account.load_key(config.PRIVATE_KEY)
    for pair in PAIRS:
        x, y = pair
        coin_x = TokenBase(x[0], x[1])
        coin_y = TokenBase(y[0], y[1])

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
        logger.success(
            'amount_in: {}, selected pool: {}, router_address: {}', amount_in, module.pool_type, module.router_address
        )


if __name__ == '__main__':
    asyncio.run(main())

