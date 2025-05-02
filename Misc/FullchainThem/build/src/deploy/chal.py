from pathlib import Path

import eth_sandbox
import eth_sandbox.launcher
from eth_typing import HexStr
from web3 import Web3
from web3.types import Wei
import json
from eth_account.signers.local import LocalAccount


# def deploy(web3: Web3, deployer_address: str, player_address: str) -> str:
#     receipt = eth_sandbox.launcher.send_transaction(
#         web3,
#         {
#             "from": deployer_address,
#             "data": json.loads(Path("/home/ctf/compiled/Setup.sol/Setup.json").read_text())["bytecode"]["object"],
#             "value": Web3.to_wei(100, "ether"),
#         },
#     )
    
#     assert receipt is not None

#     receipt_transfer = eth_sandbox.launcher.send_transaction(
#         web3,
#         {
#             "from": deployer_address,
#             "to": player_address,
#             "value": web3.to_wei(1, "ether"),
#         },
#     )

#     assert receipt_transfer is not None

#     challenge_addr = receipt["contractAddress"]
#     assert challenge_addr is not None
    
    # return challenge_addr

def deploy(web3: Web3, deployer_account: LocalAccount, deployer_address: str, player_address: str) -> dict:
    account = deployer_account

    def load_artifact(name):
        return json.loads(Path(f"/home/ctf/compiled/{name}.sol/{name}.json").read_text())

    def deploy_contract(name, args=(), value=0):
        artifact = load_artifact(name)
        contract = web3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"]["object"])
        tx = contract.constructor(*args).build_transaction({
            "from": deployer_address,
            "value": value,
            "nonce": web3.eth.get_transaction_count(deployer_address),
            "gas": 12_000_000,
            "gasPrice": web3.to_wei(1, "gwei"),
        })
        signed = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt["contractAddress"]

    # === Deploy core contracts ===
    mafia = "0xd99453Cc6931f922Ee749474bb5336d028E8B811"
    dev_token = deploy_contract("DevToken", args=(deployer_address, 10000, mafia))
    dev_lead = deploy_contract("DevLead")
    cut_facet = deploy_contract("DiamondCutFacet")
    diamond = deploy_contract("Diamond", args=(dev_lead, cut_facet))

    # === Deploy facets ===
    devkeys = [
      bytes.fromhex("ef2091a8dedb05c108f063bd79253deb368843119f44a899fb3646d725fb29c979b60c6e2edccd4474ce57c75dc61856d73611895b577caff7244674b1ea0d3a1c"),
      bytes.fromhex("523578c1dbcc7cc250a1f5a9a3e69573eea3c7a58f806a08c7a72c99810adc5b710b067134c2582e21837c393a7d881ee5e74d9932c9c170c4bc595c1d560e1c1b"),
      bytes.fromhex("037844472dc11598a36a1939820488b356ae3a2e496271fad61e7e83d7a9b20008f51cc62c6e9c12bc4fadc8319de427ccdba1514dd4d008908633f0f45e8a271b"),
      bytes.fromhex("f9baab17c6efb1f824a352c8941d659098a69e119d3b70afe59be9bbedaec0106351088f15c1613a8f4f246d505c1b2c5b77e05e9cd6f82f6d16b6778cb6db581c"),
      bytes.fromhex("c97f54dbacd1bbf6175520ca3ffdec29a3131ce0757c47cea3bf6e41432586767eb347c045c045dd908ace0ff6de26fcef27e050d304aae63263ac8283bea3201c"),
      bytes.fromhex("db0d74c6461c104ec5e3154666b85d2ab5cb4dd0515c9f8b4b4660a3803876b10be21dd65cc7fee51d98745f55f7540c447c8647a22e901173ac29b16f9d25be1c"),
      bytes.fromhex("9d68d957c952374db8ae8bd56f83173b58ad73e8ace1e042a9737bc06eea822e16d406cb0de14f049e529071bc8f6ce6f0e45cedbf2d4a52776dcc2d355043461b"),
      bytes.fromhex("2ded7eccbc0e0be6c2527afe9a4a833cb3620a1535a256240af31bf283e4266753e13ee01325672d51ab6f9b7ecdc06847566ae7adc7084dc9cdaae03685f9e61b"),
      bytes.fromhex("ddee75dc96bd34207915d34686a2bbcccf609cd0423efeb6528e09cfca9b6ed20c5a33ea21b79ec1e2beed0dbb999a5cdb2c269290ad32c71baa15dc2b59a7041b"),
      bytes.fromhex("d6987c784fd4ac6ce0203de5183679ee5e4b55af9c5a759eeb004c63fb01b8493af064001f218fe645e8cc48a5a8d9a7370dbadae493a8ed5b9ae4fb27f124ad1c"),
      bytes.fromhex("7b48d5d840ea46e33571b8339025c020ebfe459ad722591a2f4f03db1177803a7a60edb2c67898eb83e26c6efc777a29e5a3a70545e51d207d86d012d000d78d1b"),
      bytes.fromhex("9ab76db9d6dafc2714108dafb8ff0598423242fbfbe56e20bf5c77ab6f611ac74dc9e8d973d6e5a5ab10da46604e0f37f589cc21dd32c974493b89544886a0c21b"),
      bytes.fromhex("5f5026768f069bfd83c359cc9bff0e4d88a37175de030e98686a8b6b23b5280b0b5ba9b53ed123bb8160c10e0a5b4c4925429e359debb7528f654a1509c09d8a1c"),
      bytes.fromhex("f8b795ebdde30d6d109c2a6b187cebfaee97d940a90050c6c09ff50cb4fbc8750b2a4536600f95746556fd601e90909f07142036cc6ed062995c998c861c71fc1c"),
      bytes.fromhex("1bd5a8763449ff855c6f6d81e985291370de6d75914a2f59a85ce1aa95bf96707b7d2e3bce445915e401642127b4d4869398bc0ba05799878ef1538ab88099c91b"),
      bytes.fromhex("239d077ed5651e5f07a5ed309f435b5612b60f793a7b3ccf0dedf4252a1e3c9b2edf8c4a3727f89296759c78cdbdbbe2d1f5adb3ececc3f95749ef171452d1ef1b"),
      bytes.fromhex("bb7af6787221043fce7d991ffad74db7bd18a56546e3799b7a22ea979250e5915eef90cc73157d6848d29dbc8fd0b554b7574d8173a5d90113deebbade83123c1c"),
      bytes.fromhex("b581dd405502babfbe376d94355fb69c4a10eb8bebd70ef347336a2e8e99bf585cae8ad83223fb6a216213a5cdc8ba8235e32cd5be1eaa5059bf7adfd1b78e5f1c"),
      bytes.fromhex("67d7707476e9b95624b32fc17df512f438713186f37f6663f40c27d569a8892317568852abe770a1b1e8c1ade9f1ab75eb2a49aac9dbd2529c7dc5f9367ca8261c"),
      bytes.fromhex("bf631d730d7a42fe76f03af56e7a06bcae86d788ac50ec7865e973b6af23daa267d39f12affe4d797767b0d998bda2667f6c7ef2320dbd03a50a2a07252d51631b"),
    ]
    # === Deploy facets ===
    pool_facet = deploy_contract("PoolFacet", args=(devkeys, diamond,))
    loupe_facet = deploy_contract("DiamondLoupeFacet")
    rand_facet = deploy_contract("RandomizerFacet")
    money_facet = deploy_contract("MoneyGameFacet")
    refresh_facet = deploy_contract("RefreshLeaderFacet") 

    # === Fund PoolFacet with 100 ETH ===
    eth_sandbox.launcher.send_transaction(web3, {
        "from": deployer_address,
        "to": pool_facet,
        "value": web3.to_wei(100, "ether"),
    })

    # === devToken.initPoolAuthorization(address(diamond)) ===
    devtoken_abi = load_artifact("DevToken")["abi"]
    token = web3.eth.contract(address=dev_token, abi=devtoken_abi)
    tx = token.functions.initPoolAuthorization(diamond).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Transfer DevTokens to Diamond ===
    balance = token.functions.balanceOf(deployer_address).call()
    tx = token.functions.transfer(diamond, balance).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Add facets to diamond ===
    cut_abi = load_artifact("DiamondCutFacet")["abi"]
    iFacet_abi = load_artifact("IFacet")["abi"]
    diamond_cut = web3.eth.contract(address=diamond, abi=cut_abi)

    def get_selectors(facet_addr):
        facet = web3.eth.contract(address=facet_addr, abi=iFacet_abi)
        return facet.functions.getSelectors().call()

    facet_cuts = [
        {"facetAddress": loupe_facet, "action": 0, "functionSelectors": get_selectors(loupe_facet)},
        {"facetAddress": pool_facet, "action": 0, "functionSelectors": get_selectors(pool_facet)},
        {"facetAddress": rand_facet, "action": 0, "functionSelectors": get_selectors(rand_facet)},
        {"facetAddress": money_facet, "action": 0, "functionSelectors": get_selectors(money_facet)},
        {"facetAddress": refresh_facet, "action": 0, "functionSelectors": get_selectors(refresh_facet)},
    ]

    cut_input = [(cut["facetAddress"], cut["action"], cut["functionSelectors"]) for cut in facet_cuts]

    tx = diamond_cut.functions.diamondCut(
        cut_input,
        Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        b""
    ).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 5_000_000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Call setTokensAddresses() via diamond (from deployer) ===
    refresh_facet_abi = load_artifact("RefreshLeaderFacet")["abi"]
    refresh = web3.eth.contract(address=diamond, abi=refresh_facet_abi)
    tx = refresh.functions.setTokensAddresses(dev_token, dev_lead).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Call setDiamondAddr() via diamond (from deployer) ===
    money_game_facet_abi = load_artifact("MoneyGameFacet")["abi"]
    money_game = web3.eth.contract(address=diamond, abi=money_game_facet_abi)
    tx = money_game.functions.setDiamondAddr(diamond).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Call initPool() via diamond (from deployer) ===
    ppol_facet_abi = load_artifact("PoolFacet")["abi"]
    pool = web3.eth.contract(address=diamond, abi=ppol_facet_abi)
    tx = pool.functions.initPool(dev_token, dev_lead).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Transfer ownership of devLead to the Diamond ===
    devlead_abi = load_artifact("DevLead")["abi"]
    devlead_contract = web3.eth.contract(address=dev_lead, abi=devlead_abi)
    tx = devlead_contract.functions.transferOwnership(diamond).build_transaction({
        "from": deployer_address,
        "nonce": web3.eth.get_transaction_count(deployer_address),
        "gas": 100000,
        "gasPrice": web3.to_wei(1, "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    # === Send 1 ETH to player ===
    eth_sandbox.launcher.send_transaction(web3, {
        "from": deployer_address,
        "to": player_address,
        "value": web3.to_wei(1, "ether"),
    })

    # === Deploy Setup contract ===
    setup = deploy_contract(
        "Setup",
        args=(dev_token, dev_lead, diamond, pool_facet),
        value=Wei(0)
    )

    return setup



eth_sandbox.launcher.run_launcher(
    [
        eth_sandbox.launcher.new_launch_instance_action(deploy),
        eth_sandbox.launcher.new_kill_instance_action(),
        eth_sandbox.launcher.new_get_flag_action(),
    ]
)
