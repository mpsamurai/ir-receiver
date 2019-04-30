import json
import os

"""
    ファイル操作を行うクラス
"""
class Filesystem:
    """
        リモコン信号の一時ファイルへの保存を行う。
        古いファイルがあった場合は上書き。
    """
    def save_temp_file(self, signals):
        with open('tmp.ir', 'w') as f:
            f.write(json.dumps(signals, sort_keys=True).replace("],", "],\n")+"\n")

    """
        一時ファイルを永続ファイルにするために名前変更する。
    """
    def rename_tmp_file(self, name):
        pass
        
    """
        永続ファイルを削除する。
    """
    def delete_file(self, name):
        pass