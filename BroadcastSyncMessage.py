from Message import Message

class BroadcastSyncMessage(Message):
    def __init__(self, value, sender, clock):
        super().__init__(value, sender, clock)