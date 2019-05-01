import logging

logger = logging.getLogger(__name__)
IR_FOLDER_PATH = '/code'
TMP_FILE_NAME = 'tmp.ir'

"""
Mediatorクラス
Ir-receiverの各クラスはこのクラスを経由してお互い通信する。
"""
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
    def start_ir_receiving(self):
        logger.debug('Received start_ir_receiving')
        self.__redis_boundary.set_state('receiving');
        self.__redis_boundary.publish_started_ir_receiving();
        self.__respberry_pi.start_capturing_remote_signal(self.__remote_signal_received);
        
    """
        ラズパイから信号受信したときのコールバック関数
    """
    def __remote_signal_received(self, signals):
        logger.debug('Received remote signal')
        tmp_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
        self.__filesystem.save_temp_file(tmp_file_path, signals)
        logger.debug('Signals saved to tmp file {0}'.format(tmp_file_path))
        self.__redis_boundary.set_state('ready');
        self.__redis_boundary.publish_stopped_ir_receiving_valid_signal()
        
    """
        一時ファイルに保存されているリモコン信号ファイルを永続化する
    """
    def save_ir_signal(self, value):
        logger.debug('Received save_ir_signal {0}'.format(value))
        id, name, sleep = value['id'], value['name'], value['sleep']
        if(id == None):
            ir = self.__create_new_ir(name, sleep)
        else:
            ir = self.__update_current_ir(id, name, sleep)
        self.__redis_boundary.set_ir(ir)
        self.__redis_boundary.publish_stopped_ir_saving()
        
    """
        永続化されているリモコン信号ファイルとRedisからデータを削除する
    """
    def delete_ir_signal(self, id):
        logger.debug('Received delete_ir_signal {0}'.format(id))
        file_path = '{0}/{1}.ir'.format(IR_FOLDER_PATH, id)
        self.__filesystem.delete_file(file_path)
        logger.debug('Deleted signal file {0}'.format(file_path))
        ir = self.__redis_boundary.get_ir()
        new_ir = [x for x in ir["signals"] if x["id"] != id]
        self.__redis_boundary.set_ir({'signals': new_ir})
        
    """
        一時ファイルに名前をつけて永続化し、RedisにIRデータを追加して更新する
    """
    def __create_new_ir(self, name, sleep):
        ir = self.__redis_boundary.get_ir()
        logger.debug('Create new ir. Current ir is {0}'.format(ir))
        id = self.__get_largest_id(ir)
        tmp_file_path = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
        new_file_path = '{0}/{1}.ir'.format(IR_FOLDER_PATH, id)
        timestamp = self.__filesystem.rename_tmp_file(tmp_file_path, new_file_path);
        signal = {'id': id, 'name': name, 'sleep': sleep, 'filePath': new_file_path, 'fileTimeStamp': timestamp}
        if ir == None:
            ir = {'signals': []}
        ir['signals'].append(signal)
        return ir
        
    """
        Redisに格納されているIRデータを更新する
    """
    def __update_current_ir(self, id, name, sleep):
        ir = self.__redis_boundary.get_ir()
        for signal in ir['signals']:
            if signal["id"] == id:
                signal["name"] = name
                signal["sleep"] = sleep
        return ir
        
    """
        今保存されている信号の一番大きいID+1の値を新しいIDとして割り当てる
    """
    def __get_largest_id(self, ir):
        if ir == None:
            return 0
        id_list = [x['id'] for x in ir['signals']]
        if not id_list:
            return 0
        return max(id_list) + 1