from datetime import datetime
from flask import current_app


class Stats:
    __client = None

    def __init__(self, client):
        self.__client = client
        self.__client.set('stats_start_time',  int(datetime.utcnow().timestamp()))
        self.__client.set('stats_read', 0)
        self.__client.set('stats_write_del', 0)

    def get_read_requests_per_minute(self):
        start_time = self.__client.get('stats_start_time')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            start_time = datetime.utcfromtimestamp(int(start_time))

        read_requests = self.__client.get('stats_read')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            read_requests = int(read_requests)

        minutes_elapsed = (datetime.now() - start_time).total_seconds() // 60

        # too early. lets not divide by zero
        if minutes_elapsed == 0:
            minutes_elapsed = 1

        return read_requests // minutes_elapsed

    def get_write_delete_requests_per_minute(self):
        start_time = self.__client.get('stats_start_time')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            start_time = datetime.utcfromtimestamp(int(start_time))

        write_delete_requests = self.__client.get('stats_write_del')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            write_delete_requests = int(write_delete_requests)

        minutes_elapsed = (datetime.now() - start_time).total_seconds() // 60

        # too early. lets not divide by zero
        if minutes_elapsed == 0:
            minutes_elapsed = 1

        return write_delete_requests // minutes_elapsed

    def get_stats_dict(self):
        start_time = self.__client.get('stats_start_time')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            start_time = datetime.utcfromtimestamp(int(start_time))

        read_requests = self.__client.get('stats_read')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            read_requests = int(read_requests)

        write_delete_requests = self.__client.get('stats_write_del')
        if start_time is None:
            current_app.logger.error('Could not retrieve stats from database')
        else:
            write_delete_requests = int(write_delete_requests)

        minutes_elapsed = (datetime.now() - start_time).total_seconds() // 60

        # too early. lets not divide by zero
        if minutes_elapsed == 0:
            minutes_elapsed = 1

        return {'read_request_per_minute': read_requests // minutes_elapsed,
                'write_delete_requests_per_minute': write_delete_requests // minutes_elapsed}

    def increment_read_requests(self):
        self.__client.incr('stats_read')

    def increment_write_delete_requests(self):
        self.__client.incr('stats_write_del')
