from kazoo.client import KazooState
from kazoo.exceptions import NodeExistsError, ZookeeperError, NoNodeError
from kazoo.protocol.states import EventType
from multiprocessing import Condition
import json


class StorageZoo:
    _cv = Condition()

    def __init__(self, client, storage_id, znode_data):
        self._client = client
        self._storage_id = storage_id
        self._znode_data = znode_data

        self._client.start()
        self._client.add_listener(self.zoo_listener)
        self.add_storage_watcher()
        self.create_znode()

    def zoo_listener(self, state):
        if state == KazooState.LOST:
            # Register somewhere that the session was lost
            self._client.logger.warning('Session was lost')
        elif state == KazooState.SUSPENDED:
            # Handle being disconnected from Zookeeper
            self._client.logger.warning('Disconnected from Zookeeper')
        else:
            # Handle being connected/reconnected to Zookeeper
            self._client.logger.warning('Reconnected to Zookeeper')
            self._client.handler.spawn(self.create_znode)

    def create_znode(self):
        self._client.ensure_path('/storage')

        try:
            self._client.create('/storage/{}'.format(self._storage_id),
                                json.dumps(self._znode_data).encode(),
                                ephemeral=True)
        except NodeExistsError:
            # one of our brother workers has done this already
            self._client.logger.info('Znode already exists')
        except ZookeeperError:
            # other error occurred
            self._client.logger.info('Server error while creating znode')

    def get_znode(self):
        try:
            return self._client.exists("storage/{}".format(self._storage_id))
        except ZookeeperError:
            return None

    def add_storage_watcher(self):
        @self._client.DataWatch("/storage/{}".format(self._storage_id))
        def storage_watcher(data, stat, event):
            if event is not None:
                # Not in init phase
                if event.type == EventType.DELETED:
                    # We only care if the node has been deleted for now
                    self._client.logger.warning('Recreating deleted znode')
                    self.create_znode()

    def wait_for_znode(self, path):
        ret = self._client.exists(path, watch=self.watch_znode_creation)
        if ret is not None:
            return

        with self._cv:
            self._cv.wait()

    def watch_znode_creation(self, event):
        if event.type == EventType.CREATED:
            with self._cv:
                self._cv.notify_all()

    def get_znode_data(self, path):
        node = None
        try:
            node = self._client.get(path)
        except NoNodeError:
            return None
        except ZookeeperError:
            return None

        return json.loads(node[0])
