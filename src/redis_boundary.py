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
        
    """
    Redisに処理の必要があるメッセージの購読を開始する。
    """
    def subscribe(self):
        # 信号受信開始のメッセージ待ち受け
        self._start_ir_receiving = notification.StartIrReceiving(self._r)
        self._start_ir_receiving.subscribe(lambda value, channel: self.__mediator.start_ir_receiving())
        # 受信した信号の保存メッセージ待ち受け
        self._save_ir_signal = notification.SaveIrSignal(self._r)
        self._save_ir_signal.subscribe(lambda value, channel: self.__mediator.save_ir_signal(value))
        # 信号削除のメッセージ待ち受け
        self._delete_ir_signal = notification.DeleteIrSignal(self._r)
        self._delete_ir_signal.subscribe(lambda value, channel: self.__mediator.delete_ir_signal(value))
        # 信号受信の中止処理
        self._stop_ir_signal = notification.StopIrReceiving(self._r)
        self._stop_ir_signal.subscribe(lambda value, channel: self.__mediator.stop_ir_receiving())

    def unsubscribe(self):
        self._start_ir_receiving.unsubscribe()
        self._save_ir_signal.unsubscribe()
        self._delete_ir_signal.unsubscribe()
        self._stop_ir_signal.unsubscribe()

    def waits_subscriptin_end(self):
        self._start_ir_receiving.wait_subscription_end()
        self._save_ir_signal.wait_subscription_end()
        self._delete_ir_signal.wait_subscription_end()
        self._stop_ir_signal.wait_subscription_end()

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
        started_ir_receiving = notification.StartedIrReceiving(self._r)
        started_ir_receiving.value = 1 # 信号の確認機能がまだ無いので今の所、1しか存在しない
        
    def publish_stopped_ir_receiving_valid_signal(self):
        started_ir_receiving = notification.StoppedIrReceivingValidSignal(self._r)
        started_ir_receiving.value = None
        
    def publish_stopped_ir_saving(self):
        started_ir_receiving = notification.StoppedIrSaving(self._r)
        started_ir_receiving.value = None
        
    def publish_stopped_ir_saving_stop_message(self):
        started_ir_receiving = notification.StoppedIrReceivingStopMessage(self._r)
        started_ir_receiving.value = None

