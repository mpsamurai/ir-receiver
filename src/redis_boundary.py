import redis
import logging
from neochi.core.dataflow.data import ir_receiver as data
from neochi.core.dataflow import data_types
from neochi.core.dataflow.notifications import ir_receiver as notification


logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)


"""
Redisとの通信を行うクラス
Redisへのアクセスはこのクラスに閉じている。
"""


class RedisBoundary:
    
    def __init__(self, mediator):
        self._r = redis.StrictRedis('localhost')
        self.__mediator = mediator
        self._neochi_app_ir_receiver = None
        
    """
    Redisに処理の必要があるメッセージの購読を開始する。
    """
    def subscribe(self):
        # neochi-appからのメッセージ待ち受け
        self._neochi_app_ir_receiver = notification.NeochiAppIrReceiver(self._r)
        self._neochi_app_ir_receiver.subscribe(lambda value, channel: self.__mediator.on_receive_message(value))

    def unsubscribe(self):
        self._neochi_app_ir_receiver.unsubscribe()

    def waits_subscription_end(self):
        self._neochi_app_ir_receiver.wait_subscription_end()

    """
    現在のIr-reciverの状態を取得する
    """
    def get_state(self):
        state = data.State(self._r)
        return state.value
        
    """
    現在のIr-reciverの状態を設定する
    """
    def set_state(self, new_state):
        state = data.State(self._r)
        state.value = new_state
        
    """
    Redisに格納されている最新のIRを取得する
    """
    def get_ir(self):
        ir = data.Ir(self._r)
        return ir.value
    
    """
    Redisに最新のIR情報を設定する
    """
    def set_ir(self, new_ir):
        ir = data.Ir(self._r)
        ir.value = new_ir

    def publish_started_ir_receiving(self):
        n = notification.IrReceiverNeochiApp(self._r)
        # 信号の確認機能がまだ無いので今の所indexは0しか存在しない
        n.value = {'title': 'started_ir_receiving', 'index': 0}

    def publish_stopped_ir_receiving_no_signal(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'stopped_ir_receiving_no_signal'}

    def publish_stopped_ir_receiving_invalid_signal(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'stopped_ir_receiving_invalid_signal'}

    def publish_stopped_ir_receiving_valid_signal(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'stopped_ir_receiving_valid_signal'}

    def publish_stopped_ir_receiving_stop_message(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'stopped_ir_receiving_stop_message'}

    def publish_stopped_ir_receiving_more_signal(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'stopped_ir_receiving_more_signal'}

    def publish_saved_ir_signal(self, ir_signal_id):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'saved_ir_signal', 'id': ir_signal_id}

    def publish_ir_signal_saving_error(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'ir_signal_saving_error'}

    def publish_discarded_ir_signal(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'discarded_ir_signal'}

    def publish_ir_signal_discarding_error(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'ir_signal_discarding_error'}

    def publish_deleted_ir_signal(self, ir_signal_id):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'deleted_ir_signal', 'id': ir_signal_id}

    def publish_ir_signal_deleting_error(self):
        n = notification.IrReceiverNeochiApp(self._r)
        n.value = {'title': 'ir_signal_deleting_error'}
