import tempfile
import json
import os
from settings import Directories
from threading import Lock


class ReadWrite:
    lock = Lock()

    @classmethod
    def write(cls, payload, file):
        os.chdir(Directories.DATA_DIR)
        file = f"{file}.json"
        with cls.lock:
            with tempfile.TemporaryFile(mode="rb+") as tmpf:
                if os.path.isfile(file):
                    file_exists = True
                else:
                    file_exists = False

                # Backup old data
                if file_exists:
                    with open(file, "rb") as f:
                        tmpf.write(f.read())

                # noinspection PyBroadException
                try:
                    with open(file, "w") as f:
                        f.write(json.dumps(payload, indent=4))

                except Exception as e:
                    # Restore old data
                    if file_exists:
                        with open(file, "wb") as f:
                            tmpf.seek(0)
                            f.write(tmpf.read())
                    raise e

                finally:
                    os.chdir(Directories.ROOT_DIR)

    @classmethod
    def read(cls, file):
        os.chdir(Directories.DATA_DIR)
        file = rf'{os.getcwd()}\{file}.json'
        with cls.lock:
            # noinspection PyBroadException
            try:
                with open(file, "r")as f:
                    payload = json.loads(f.read())
            except Exception as e:
                print(e)
                payload = dict()
            finally:
                os.chdir(Directories.ROOT_DIR)
                return payload


if __name__ == '__main__':
    pass
