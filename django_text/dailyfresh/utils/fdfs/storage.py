from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FDFSStorage(Storage):
    def __init__(self, client_conf=None, base_address=None):
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
            self.client_conf = client_conf
        if base_address is None:
            base_address = settings.FDFS_URL
            self.base_address = base_address

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        client = Fdfs_client(self.client_conf)
        res = client.upload_by_buffer(content.read())
        if res.get('Status') != 'Upload successd.':
            raise Exception('文件上传失败')
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        return False

    def url(self, name):

        #name是nginx给该文件的id
        return self.base_address + name
