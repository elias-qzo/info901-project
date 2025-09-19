from SystemMessage import SystemMessage

class SyncAck(SystemMessage):
    def __init__(self, to):
        super().__init__(to)