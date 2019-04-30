import redis
import logging
from neochi.core.dataflow.data import ir_receiver as data
from neochi.core.dataflow import data_types
from neochi.core.dataflow.notifications import ir_receiver as notification


    
logger = logging.getLogger(__name__)
    

class RedisBoundary:
    
    def __init__(self, mediator):
        self._r = redis.StrictRedis('redis')
        self.__mediator = mediator
        
    def subscribe(self):
        start_ir_receiving = notification.StartIrReceiving(self._r)
        start_ir_receiving.subscribe(lambda count: self.__mediator.start_ir_receiving(count))
        
    def set_state(self, new_state):
        state = data.State(self._r)
        state.value = new_state
        
    def get_ir(self):
        ir = data.Ir(self._r)
        return ir.get()
        
    def set_ir(self, new_ir):
        ir = data.Ir(self._r)
        ir.value = new_ir
        
    def publish_started_ir_receiving(self):
        started_ir_receiving = notification.StartedIrReceiving(self._r)
        started_ir_receiving.value = 1 # 信号の確認機能がまだ無いので今の所、1しか存在しない
        
    def publish_stopped_ir_receiving_valid_signal(self):
        started_ir_receiving = notification.StoppedIrReceivingValidSignal(self._r)
        started_ir_receiving.value = None