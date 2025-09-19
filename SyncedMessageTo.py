from MessageTo import MessageTo

class SyncedMessageTo(MessageTo):
    def __init__(self, value, sender, to, clock):
        super().__init__(value, sender, to, clock)
        self.to = to
        self.sender = sender
    
    def getTo(self):
        return self.to