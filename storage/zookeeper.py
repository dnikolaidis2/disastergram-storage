from kazoo.client import KazooState
from kazoo.exceptions import NodeExistsError, ZookeeperError
from kazoo.protocol.states import EventType
import json


class StorageZoo:
    _background_thread = None

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
            self._client.logger.warning('Is there anybody out there')
            if event is not None:
                # Not in init phase
                if event.type == EventType.DELETED:
                    # We only care if the node has been deleted for now
                    self.create_znode()
