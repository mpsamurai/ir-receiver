# MIT License
#
# Copyright (c) 2019 Morning Project Samurai (MPS)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import json
import os
import unittest
import logging
import redis_boundary
import filesystem
import mediator

IR_FOLDER_PATH = '/code'
TMP_FILE_NAME = 'tmp.ir'

logger = logging.getLogger(__name__)
test_signal = {"ac:cool27": [8970, 4475, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 39710, 8970, 2265, 586]}
test_signal_string = '{"ac:cool27": [8970, 4475, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 544, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 1669, 586, 39710, 8970, 2265, 586]}'


"""
ラズパイ依存の部分は自作モックで代用
"""
class RespberryPiBoundaryMock():
    def start_capturing_remote_signal(self, callback):
        callback(test_signal, False)

class TestMediator(unittest.TestCase):

    def setUp(self):
        self.__mediator = mediator.Mediator()
        self.__redis_boundary = redis_boundary.RedisBoundary(self.__mediator)
        self.__filesystem = filesystem.Filesystem()
        self.__raspberry_pi = RespberryPiBoundaryMock()
        self.__mediator.initialize(self.__redis_boundary, self.__filesystem, self.__raspberry_pi)
        # サービスの開始
        self.__mediator.start()

    """
    リモコン信号受信の一覧の流れをテスト
    """
    def test_start_ir_receiving(self):
        """
        start_ir_receivingメッセージを受けて下記のアクションが完了していること確認。
        １．stateがreadyに戻っている
        ２．受信した信号が一時ファイルに保存されている。
        """
        logger.debug("Testing Signal creation")
        self.__mediator.start_ir_receiving()
        assert self.__redis_boundary.get_state() == 'ready'
        tmp_file_name = '{0}/{1}'.format(IR_FOLDER_PATH, TMP_FILE_NAME)
        assert self.__filesystem.get_file(tmp_file_name) == test_signal_string

        """
        新規信号としてのsave_ir_signalメッセージを受けて下記のアクションが完了していること確認。
        １．stateがreadyに戻っている
        ２．指定のファイルが永続化されている
        ３．redisに信号ファイルの情報が保存されている
        """
        logger.debug("Testing Signal save")
        signal = {'id': None, 'name': 'test_signal', 'sleep': 200}
        self.__mediator.save_ir_signal(signal)
        signal["id"] = 0
        new_file_path = '{0}/{1}.ir'.format(IR_FOLDER_PATH, signal["id"])
        assert self.__redis_boundary.get_state() == 'ready'
        assert self.__filesystem.get_file(new_file_path) == test_signal_string
        #assert self.__redis_boundary.get_ir() == {'signals': [signal]}
        
        """
        信号の更新としてのsave_ir_signalメッセージを受けて下記のアクションが完了していること確認。
        １．stateがreadyに戻っている
        ２．redisデータが指定の内容で更新されている
        """
        logger.debug("Testing Signal update")
        new_signal = {'id': 0, 'name': 'test_signal_updated', 'sleep': 300}
        self.__mediator.save_ir_signal(new_signal)
        assert self.__redis_boundary.get_state() == 'ready'
        #assert self.__redis_boundary.get_ir() == {'signals': [new_signal]}
        
        """
        delete_ir_signalメッセージを受けて下記のアクションが完了していること確認。
        １．stateがreadyに戻っている
        ２．指定の信号ファイルが削除されている
        ３．指定のredisデータが削除されている
        """
        logger.debug("Testing Signal deletion")
        self.__mediator.delete_ir_signal(0)
        logger.debug(self.__redis_boundary.get_ir())
        assert self.__redis_boundary.get_state() == 'ready'
        assert not os.path.exists(new_file_path)
        assert self.__redis_boundary.get_ir() == {'signals': []}
        
    """
    リモコン信号受信中止をテスト
    """
    def test_stop_ir_receiving(self):
        self.__mediator.remote_signal_received([], True)