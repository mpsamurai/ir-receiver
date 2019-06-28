import logging
import redis_boundary
import filesystem
import raspberry_pi_boundary
import mediator
import time

if __name__ == '__main__':
    logging.basicConfig(filename='logs/ir_receiver.log', level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    
        #各種コンポーネントの初期化
    logger.debug('Received ir_receiver service starting')
    __mediator = mediator.Mediator();
    __redis_boundary = redis_boundary.RedisBoundary(__mediator);
    __filesystem = filesystem.Filesystem();
    __raspberry_pi = raspberry_pi_boundary.RespberryPiBoundary();
    __mediator.initialize(__redis_boundary, __filesystem, __raspberry_pi)

    try:
        # サービスの開始
        __mediator.start()
        logger.debug('Received ir_receiver service started')

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.debug('KeyboardInterrupt')
        __mediator.stop()

        # neochi-core issues #20 待ち
        #__mediator.wait_stop_end()

        logger.debug('Received ir_receiver service ended')
