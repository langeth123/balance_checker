from config import *
import traceback

def get_all_tickers():
    def __req__():
        try:
            resp = requests.get("https://api.binance.com/api/v3/ticker/price")
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f'Cant fetch prices data from binance')
        except Exception as error:
            logger.error(f"Requests error: {error}")
    
    while True:
        logger.info("Getting info about all tickers from Binance")
        resp = __req__()
        if resp is None: sleep(5)
        else: 
            data = {}
            for pair in resp:
                if pair["symbol"] in SUPPORTED_TICKERS:
                    if "BNB" in pair["symbol"]:
                        ticker = 'BSC'
                    else:
                        ticker = pair["symbol"].split("USDT")[0]
                    data.update(
                        {
                            ticker: float(pair["price"])
                        }
                    )
            logger.success("All Binance data was fetched")
            return data


PRICES  = get_all_tickers()

async def check_data_token(token_address: str, net_name: str):
    try:
        web3 = choice(CONNECTED_RPCS[net_name])
        address = Web3.to_checksum_address(token_address)

        token_contract  = web3.eth.contract(address=address, abi=ERC20_ABI)
        decimals        = await token_contract.functions.decimals().call()

        return token_contract, decimals
    
    except Exception as error:
        if 'Too Many Requests' in str(error):
            logger.error(f'{net_name} - Ratelimited! Thread sleeping 15-30 seconds')
            await asyncio.sleep(randint(15, 30))
        else:
            logger.error(f'[{token_address}] | {error}')
            await asyncio.sleep(2)
        return await check_data_token(token_address, net_name)

async def check_balance(way='stable', **kwargs):
    try:
        net_name, wallet = kwargs["net_name"], Web3.to_checksum_address(kwargs["wallet"])
        web3 = choice(CONNECTED_RPCS[net_name])
        if way == 'stable':

            token_contract, token_decimal = await check_data_token(kwargs["token_address"], net_name)
            balance = await token_contract.functions.balanceOf(wallet).call()
        else:
            token_decimal = 0
            balance = await web3.eth.get_balance(wallet)

        return {"net_name": net_name, "balance": balance, 'decimal': token_decimal}

    except Exception as error:
        if 'Too Many Requests' in str(error):
            logger.error(f'[{wallet}] {net_name} - Ratelimited! Thread sleeping 1-5 seconds')
            await asyncio.sleep(3)
        else:
            logger.error(f'[{wallet}] | {error}')
            await asyncio.sleep(2)
        return await check_balance(way=way, **kwargs)


async def checker(address):
    tokes_res = []
    logger.info(f"[{address}] Start checking: {''.join(f'{token} ' for token in TOKENS.keys())}")

    for token_name in TOKENS.keys():
        tasks, data = [], {"wallet": address}

        for net_name in TOKENS[token_name]:
            data.update({"net_name": net_name, "token_address": TOKENS[token_name][net_name]})
            tasks.append(asyncio.create_task(check_balance(**data)))

        tokes_res.append({"token_name": token_name, 'res': await asyncio.gather(*tasks)})
        logger.info(f'[{address}] | Got info about: {token_name}')

    logger.success(f"[{address}] All tokens was fetched! Start checking native currencies")

    tasks = [asyncio.create_task(
        check_balance(way='s', **{"wallet": address, "net_name": net_name})
    )   for net_name in CONNECTED_RPCS.keys()]
    
    return {
        "address": address,
        "data": await asyncio.gather(*tasks),
        "tokens": tokes_res
    }


async def start_handler():
    tasks = [asyncio.create_task(checker(wallet)) for wallet in WALLETS
             if await asyncio.sleep(DELAY) is None]
    
    result = []
    for l in tasks:
        while True:
            try:
                result.append(l.result())
                break
            except asyncio.exceptions.InvalidStateError:
                logger.debug("waaiting")
                await asyncio.sleep(1)

    with open('some.csv', 'w', newline='') as csvfile:
        fieldnames = []
        for i in FIELDS:
            for x in i:
                fieldnames.append(x)
                
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for item in result:
            temp_data = {'ADDRESS': item["address"]}
            for field in item['data']:
                balance = Web3.from_wei(field["balance"], 'ether')
                temp_data.update({f'{field["net_name"]}_N': str(round(balance, 4)).replace(".", ',')})
            
            for field in item['tokens']:
                name = field.get("token_name")
                for i in field["res"]:
                    balance = i["balance"]
                    if balance != 0:
                        balance = balance / 10**i["decimal"]

                    if name == "BTCB":
                        balance = round(balance, 7)
                    else:
                        balance = round(balance, 2)
                    temp_data.update({f'{i["net_name"]}_{name}': str(balance).replace(".", ',')})
            
            stable_amount = 0
            for x in [usdc_fields, usdt_fields]:
                stable_amount += sum([float(temp_data[i].replace(",", '.')) for i in x])

            btcb_amount = sum([float(temp_data[i].replace(",", '.')) for i in btcb_fields])
            eth_amount = sum([float(temp_data[i].replace(",", '.')) for i in ["ETH_N", "ARB_N", "ZKSYNC_N"]])
            ftm_balance, matic_balance, avax_balance = temp_data["FTM_N"], temp_data["MATIC_N"], temp_data["AVAX_N"]
            bsc_balance = temp_data["BSC_N"]

            all_balance_usd = round(float(btcb_amount) * PRICES["BTC"] + float(eth_amount) * PRICES["ETH"] +
                               float(ftm_balance.replace(",", '.')) * PRICES["FTM"] + float(matic_balance.replace(",", '.')) * PRICES["MATIC"] +
                               float(avax_balance.replace(",", '.')) * PRICES["AVAX"] + stable_amount + 
                               float(bsc_balance.replace(",", '.')) * PRICES["BSC"], 2)
    

            logger.info(f'[{item["address"]}] STABLES: {round(stable_amount, 2)} | BTCB: {btcb_amount}\n' +
                        f'FTM: {ftm_balance} | MATIC: {matic_balance} | AVAX: {avax_balance} | ' + 
                        f"Balance in usd: {all_balance_usd}")
            
            temp_data.update({"USD_BALANCE": str(all_balance_usd).replace(".", ',')})

            writer.writerow(temp_data)


    