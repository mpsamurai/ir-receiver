import logging

logger = logging.getLogger(__name__)

class Mediator:
    
    def initialize(self, redis_boundary, filesystem, respberry_pi):
        self.__redis_boundary = redis_boundary
        self.__redis_boundary.set_state('booting');
        self.__filesystem = filesystem
        self.__respberry_pi = respberry_pi
        
    def start(self):
        # Redisデータの受付開始
        self.__redis_boundary.subscribe()
        self.__redis_boundary.set_state('ready');
        
    """
        ラズパイからリモコン信号のキャプチャを開始する。
    """
    def start_ir_receiving(self, count):
        logger.debug('Received start_ir_receiving')
        self.__redis_boundary.set_state('receiving');
        self.__redis_boundary.publish_started_ir_receiving();
        self.__respberry_pi.start_capturing_remote_signal(self.__remote_signal_received);
        
    """
        ラズパイから信号受信したときのコールバック関数
    """
    def __remote_signal_received(self, signals):
        logger.debug('Received remote signal')
        self.__filesystem.save_temp_file(signals)
        logger.debug('Signals saved to tmp file')
        self.__redis_boundary.set_state('ready');
        self.__redis_boundary.publish_stopped_ir_receiving_valid_signal()