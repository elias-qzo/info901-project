import json

class Message:
    def __init__(self, value, sender, clock):
        self.value = value
        self.sender = sender
        self.clock = clock
    
    def getValue(self):
        return self.value

    def setClock(self, clock):
        self.clock = clock

    def getClock(self):
        return self.clock
    
    def getSender(self):
        return self.sender
