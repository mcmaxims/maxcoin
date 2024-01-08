from pyteal import *


def max_token_contract():
    # Konstanten
    max_token_id = Int(123456)  # Tatsächliche Asset-ID von MAX
    liquidity_pool_address = Addr("2PIFZW53RHCSFSYMCFUBW4XOCXOMB7XOYQSQ6KGT3KVGJTL4HM6COZRNMM")  # Adresse des Liquidity Pools
    tinyman_amm_v2_app_id = Int(148607000)  # Tinyman AMM v2 App-ID

    # Transaktionen
    receive_algo_txn = Gtxn[0]
    send_max_txn = Gtxn[1]
    asset_transfer_to_pool_txn = Gtxn[2]
    app_call_txn = Gtxn[3]

    # Group Transaction Validation
    is_correct_group = And(
        receive_algo_txn.group_index() == Int(0),
        send_max_txn.group_index() == Int(1),
        asset_transfer_to_pool_txn.group_index() == Int(2),
        app_call_txn.group_index() == Int(3),
        Global.group_size() == Int(4)
    )

    # Gebühren und Mindestguthaben
    sufficient_fees = Global.min_txn_fee() * Global.group_size() <= receive_algo_txn.fee()

    # Empfangen von Algos
    is_receive_algo_txn = And(
        receive_algo_txn.type_enum() == TxnType.Payment,
        receive_algo_txn.receiver() == Global.current_application_address(),
        receive_algo_txn.amount() == Int(1000000)  # 1 Algo in Mikroalgos
    )

    # Senden von MAX-Token
    is_send_max_txn = And(
        send_max_txn.type_enum() == TxnType.AssetTransfer,
        send_max_txn.xfer_asset() == max_token_id,
        send_max_txn.asset_amount() == Int(1),
        send_max_txn.asset_receiver() == receive_algo_txn.sender()
    )

    # Hinzufügen von Liquidität zum Pool
    is_add_liquidity_txn = And(
        asset_transfer_to_pool_txn.type_enum() == TxnType.AssetTransfer,
        asset_transfer_to_pool_txn.xfer_asset() == max_token_id,
        asset_transfer_to_pool_txn.asset_amount() == Int(1),
        asset_transfer_to_pool_txn.asset_receiver() == liquidity_pool_address,

        app_call_txn.type_enum() == TxnType.ApplicationCall,
        app_call_txn.application_id() == tinyman_amm_v2_app_id,
        app_call_txn.on_completion() == OnComplete.NoOp,
        app_call_txn.application_args[0] == Bytes("add_initial_liquidity"),
        app_call_txn.accounts[0] == liquidity_pool_address
    )

    # Gesamte Transaktionslogik
    transfer_logic = And(
        is_correct_group,
        sufficient_fees,
        is_receive_algo_txn,
        is_send_max_txn,
        is_add_liquidity_txn
    )

    return transfer_logic


if __name__ == "__main__":
    print(compileTeal(max_token_contract(), mode=Mode.Signature, version=5))

