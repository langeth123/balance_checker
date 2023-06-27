from config import *
from Scripts.parser import start_handler


async def connect_to_all_rpcs():
    for net_name in RPC.keys():
        temp = []

        for i in RPC[net_name]:
            web3 = Web3(
                AsyncHTTPProvider(i),
                modules={"eth": (AsyncEth,)},
                middlewares=[],
            )
            temp.append(web3)
        
        CONNECTED_RPCS.update({net_name: temp})
    logger.success("Soft connected to all rpc's")



def main():
    asyncio.run(connect_to_all_rpcs())
    asyncio.run(start_handler())


if __name__ == "__main__":
    main()