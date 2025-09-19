from Message import Message

class MessageTo(Message):
    def __init__(self, value, sender, to, clock):
        super().__init__(value, sender, clock)
        self.to = to
        self.sender = sender
    
    def getTo(self):
        return self.to