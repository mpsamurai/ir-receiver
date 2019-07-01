import logging

logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
logger.addHandler(sh)
IR_FOLDER_PATH = '/data' # このパスはDockerコンテナの信号ファイル・ディレクトリのマウント時に揃える必要があるので注意
TMP_FILE_NAME = 'tmp.ir'

"""
Mediatorクラス
Ir-receiverの各クラスはこのクラスを経由してお互い通信する。
"""


class Mediator:
    def __init__(self):
        self.__redis_boundary = None
        self.__filesystem = None
        self.__raspberry_pi = None

    def initialize(self, redis_boundary, filesystem, raspberry_pi):
        self.__redis_boundary = redis_boundary
        self.__redis_boundary.set_state('booting')
        self.__filesystem = filesystem
        self.__raspberry_pi = raspberry_pi
        
    def start(self):
        # Redisデータの受付開始
        self.__redis_boundary.subscribe()
        self.__redis_boundary.set_state('ready')

    def stop(self):
        self.__redis_boundary.unsubscribe()

    def wait_stop_end(self):
        self.__redis_boundary.waits_subscription_end()

    def on_receive_message(self, value):
        title = value['title']
        if title == 'start_ir_receiving':
            self.__start_ir_receiving(value)
        elif title == 'stop_ir_receiving':
            self.__stop_ir_receiving(value)
        elif title == 'save_ir_signal':
            self.__save_ir_signal(value)
        elif title == 'discard_ir_signal':
            self.__discard_ir_signal(value)
        elif title == 'delete_ir_signal':
            self.__delete_ir_signal(value)

    """
        ラズパイからリモコン信号のキャプチャを開始する。
    """
    def __start_ir_receiving(self, value):
        logger.debug('Received start_ir_receiving')
        self.__redis_boundary.set_state('receiving')
        self.__redis_boundary.publish_started_ir_receiving()
        self.__raspberry_pi.start_capturing_remote_signal(self.remote_signal_received)

    """
        リモコンの信号受信を中止する
    """
    def __stop_ir_receiving(self, value):
        self.__raspberry_pi.stop_capturing_remote_signal()

    """
        一時ファイルに保存されているリモコン信号ファイルを永続化する
    """
    def __save_ir_signal(self, value):
        logger.debug('Received save_ir_signal {0}'.format(value))
        ir_signal_id, name, sleep, updates_file = value['id'], value['name'], value['sleep'], value['updatesFile']
        if ir_signal_id is None:
            ir_signal_id = self.__create_new_ir(name, sleep, updates_file)
        else:
            self.__update_current_ir(ir_signal_id, name, sleep, updates_file)
        self.__redis_boundary.publish_saved_ir_signal(ir_signal_id)

    """
        一時ファイルに保存されているリモコン信号ファイルを破棄する
    """
    def __discard_ir_signal(self, value):
        # TODO 実装
        self.__redis_boundary.publish_discarded_ir_signal()

    """
        永続化されているリモコン信号ファイルとRedisからデータを削除する
    """
    def __delete_ir_signal(self, value):
        ir_signal_id = value['id']
        logger.debug('Received delete_ir_signal {0}'.format(ir_signal_id))
        file_path = '{0}/{1}.ir'.format(IR_FOLDER_PATH, ir_signal_id)
        self.__filesystem.delete_file(file_path)
        logger.debug('Deleted signal file {0}'.format(file_path))
        ir = self.__redis_boundary.get_ir()
        new_ir = [x for x in ir["signals"] if x["id"] != ir_signal_id]
        self.__redis_boundary.set_ir({'signals': new_ir})
        self.__redis_boundary.publish_deleted_ir_signal(ir_signal_id)

    """
        ラズパイから信号受信したときのコールバック関数
    """
    def remote_signal_received(self, signals, cancelled):
        logger.debug('Received remote signal')
        self.__redis_boundary.set_state('ready')
        if cancelled:
            self.__redis_boundary.publish_stopped_ir_receiving_stop_message()
            return
        tmp_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
        self.__filesystem.save_temp_file(tmp_file_path, signals)
        logger.debug('Signals saved to tmp file {0}'.format(tmp_file_path))
        self.__redis_boundary.publish_stopped_ir_receiving_valid_signal()

    """
        一時ファイルに名前をつけて永続化し、RedisにIRデータを追加して更新する
    """
    def __create_new_ir(self, name, sleep, updates_file):
        ir = self.__redis_boundary.get_ir()
        logger.debug('Create new ir. Current ir is {0}'.format(ir))
        ir_signal_id = self.__get_new_ir_signal_id(ir)

        new_file_name = None
        timestamp = None
        if updates_file:
            tmp_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
            new_file_name = '{0}.ir'.format(ir_signal_id)
            new_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, new_file_name)
            timestamp = self.__filesystem.rename_tmp_file(tmp_file_path, new_file_path)
        signal = {'id': ir_signal_id, 'name': name, 'sleep': sleep,
                  'filePath': new_file_name, 'fileTimeStamp': timestamp}
        if ir is None:
            ir = {'signals': []}
        ir['signals'].append(signal)
        self.__redis_boundary.set_ir(ir)
        return ir_signal_id
        
    """
        Redisに格納されているIRデータを更新する
    """
    def __update_current_ir(self, ir_signal_id, name, sleep, updates_file):
        ir = self.__redis_boundary.get_ir()
        is_signal_updated = False
        for signal in ir['signals']:
            if signal["id"] == ir_signal_id:
                signal["name"] = name
                signal["sleep"] = sleep
                if updates_file:
                    tmp_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
                    new_file_name = '{0}.ir'.format(ir_signal_id)
                    new_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, new_file_name)
                    timestamp = self.__filesystem.rename_tmp_file(tmp_file_path, new_file_path)
                    signal['filePath'] = new_file_name,
                    signal['fileTimeStamp'] = timestamp
                is_signal_updated = True
                logger.debug('__update_current_ir() updated. signal:{0}'.format(signal))
        if is_signal_updated:
            self.__redis_boundary.set_ir(ir)


    """
        今保存されている信号の一番大きいID+1の値を新しいIDとして割り当てる
    """
    def __get_new_ir_signal_id(self, ir):
        if ir is None:
            return 0
        id_list = [x['id'] for x in ir['signals']]
        if not id_list:
            return 0
        return max(id_list) + 1

