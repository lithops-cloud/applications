import io
import os as base_os
from cloudbutton import CloudStorage

_cloud_storage = CloudStorage()
globals().update(base_os.__dict__)

class CloudFileProxy:
    def __init__(self, filename, mode='r', cloud_storage=None):
        self.cs = cloud_storage or _cloud_storage
        self.key = filename
        self.mode = mode
        self.buf = None

    def __enter__(self):
        if 'r' in self.mode:
            self.buf = io.BytesIO(self.cs.get_data(self.key))
            return self.buf
        return self

    def __exit__(self, *args):
        self.key = None
        if self.buf is not None:
            try:
                self.buf.close()
            except:
                pass

    def write(self, data):
        self.cs.put_data(self.key, data)

def open(filename, mode='r'):
    return CloudFileProxy(filename, mode)

def listdir(path):
    return [base_os.path.basename(name) for name in _cloud_storage.list_tmp_data(prefix=path)]

def remove(key):
    _cloud_storage.delete_cobject(key=key)
