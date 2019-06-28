import json
import os

"""
    ファイル操作を行うクラス
"""
class Filesystem:
    def get_file(self, name):
        with open(name) as f:
            return f.read();
    """
        リモコン信号の一時ファイルへの保存を行う。
        古いファイルがあった場合は上書き。
    """
    def save_temp_file(self, name, signals):
        with open(name, 'w') as f:
            f.write(json.dumps(signals))

    """
        一時ファイルを永続ファイルにするために名前変更する。
        名前変更後は最終更新日付をエポック時間で返す
    """
    def rename_tmp_file(self, name, new_name):
        os.rename(name, new_name)
        return os.path.getmtime(new_name)
        
    """
        永続ファイルを削除する。
    """
    def delete_file(self, name):
        if os.path.exists(name):
            os.remove(name)