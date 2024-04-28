from typing import Union

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from loguru import logger

from base import ModuleBase
from contracts.base import TokenBase
from utils.math import get_coins_out_with_fees_stable, d, get_coins_out_with_fees


class LiquidSwapCurve(ModuleBase):
    def __init__(
            self,
            account: Account,
            base_url: str,
            coin_x: TokenBase,
            coin_y: TokenBase,
            proxies: dict = None
    ):
        super().__init__(
            coin_x=coin_x,
            coin_y=coin_y,
            base_url=base_url,
            account=account,
            proxies=proxies
        )

        self.account = account
        self.router_address = AccountAddress.from_str(
            "0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12"
        )

        self.resource_data = None
        self.pool_type = None

    async def get_token_pair_reserve(self, pool_type: str) -> Union[dict, None]:
        #https://aptos-mainnet.pontem.network/v1/accounts/
        # 0x05a97986a9d031c4567e15b797be516910cfcb4156312482efc6a19c0a30c948/resource/
        # 0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::liquidity_pool::LiquidityPool
        # %3C0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC,
        # 0x1::aptos_coin::AptosCoin,
        # 0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Uncorrelated%3E
        resource_acc_address = AccountAddress.from_str(
            "0x05a97986a9d031c4567e15b797be516910cfcb4156312482efc6a19c0a30c948"
        )

        res_payload = f"{self.router_address}::liquidity_pool::LiquidityPool" \
                      f"<{self.coin_x.contract_address}, {self.coin_y.contract_address}, " \
                      f"{self.router_address}::curves::{pool_type}>"

        resource_data = await self.get_token_reserve(
            resource_address=resource_acc_address,
            payload=res_payload
        )

        if resource_data is not None:
            self.resource_data = resource_data

            reserve_x = resource_data["data"]["coin_x_reserve"]["value"]
            reserve_y = resource_data["data"]["coin_y_reserve"]["value"]

            return {
                self.coin_x.contract_address: reserve_x,
                self.coin_y.contract_address: reserve_y
            }

        else:

            res_payload = f"{self.router_address}::liquidity_pool::LiquidityPool" \
                          f"<{self.coin_y.contract_address}, {self.coin_x.contract_address}, " \
                          f"{self.router_address}::curves::{pool_type}>"

            reversed_data = await self.get_token_reserve(
                resource_address=resource_acc_address,
                payload=res_payload
            )
            if reversed_data is None:
                logger.error(f"Error getting token pair reserve (reverse), {pool_type} pool")
                return None

            self.resource_data = reversed_data
            reserve_x = reversed_data["data"]["coin_x_reserve"]["value"]
            reserve_y = reversed_data["data"]["coin_y_reserve"]["value"]

            return {
                self.coin_x.contract_address: reserve_y,
                self.coin_y.contract_address: reserve_x
            }

    async def get_amount_in_stable_pool(
            self,
            amount_out: int,
            coin_x_address: str,
            coin_y_address: str,
            coin_x_decimals: int,
            coin_y_decimals: int
    ) -> Union[int, None]:
        tokens_reserve: dict = await self.get_token_pair_reserve(pool_type="Stable")
        if tokens_reserve is None:
            return None

        reserve_x = int(tokens_reserve[coin_x_address])
        reserve_y = int(tokens_reserve[coin_y_address])

        if reserve_x is None or reserve_y is None:
            return None

        pool_fee = int(self.resource_data["data"]["fee"])

        amount_in = get_coins_out_with_fees_stable(
            coin_in=d(amount_out),
            reserve_in=d(reserve_x),
            reserve_out=d(reserve_y),
            scale_in=d(pow(10, coin_x_decimals)),
            scale_out=d(pow(10, coin_y_decimals)),
            fee=d(pool_fee)
        )

        return int(amount_in)

    async def get_amount_in_uncorrelated_pool(
            self,
            amount_out: int,
            coin_x_address: str,
            coin_y_address: str,
    ) -> Union[int, None]:
        tokens_reserve: dict = await self.get_token_pair_reserve(pool_type="Uncorrelated")

        if tokens_reserve is None:
            return None

        reserve_x = int(tokens_reserve[coin_x_address])
        reserve_y = int(tokens_reserve[coin_y_address])

        if reserve_x is None or reserve_y is None:
            return None

        pool_fee = int(self.resource_data["data"]["fee"])

        amount_in = get_coins_out_with_fees(
            coin_in_val=d(amount_out),
            reserve_in=d(reserve_x),
            reserve_out=d(reserve_y),
            fee=d(pool_fee)
        )

        return amount_in

    async def get_most_profitable_amount_in_and_set_pool_type(
            self,
            amount_out: int,
            coin_x_address: str,
            coin_y_address: str,
            coin_x_decimals: int,
            coin_y_decimals: int
    ):
        stable_pool_amount_in = await self.get_amount_in_stable_pool(
            amount_out=amount_out,
            coin_x_address=coin_x_address,
            coin_y_address=coin_y_address,
            coin_x_decimals=coin_x_decimals,
            coin_y_decimals=coin_y_decimals
        )
        logger.debug('stable_pool_amount_in: {}', stable_pool_amount_in)

        if stable_pool_amount_in is None:
            return None

        uncorrelated_pool_amount_in = await self.get_amount_in_uncorrelated_pool(
            amount_out=amount_out,
            coin_x_address=coin_x_address,
            coin_y_address=coin_y_address
        )
        logger.debug('uncorrelated_pool_amount_in: {}', uncorrelated_pool_amount_in)

        if uncorrelated_pool_amount_in is None:
            return None

        if stable_pool_amount_in > uncorrelated_pool_amount_in:
            self.pool_type = "Stable"
            return stable_pool_amount_in

        self.pool_type = "Uncorrelated"
        return uncorrelated_pool_amount_in
