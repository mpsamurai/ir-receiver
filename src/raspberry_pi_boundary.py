import logging

logger = logging.getLogger(__name__)

class RespberryPiBoundary:
        
    def start_capturing_remote_signal(self, callback):
        logger.debug('Start capturing remote signal')
        callback({})
        
    def stop_capturing_remote_signal(self):
        pass