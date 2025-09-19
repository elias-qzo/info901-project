import queue

class Mailbox:
    def __init__(self):
        self.queue = queue.Queue()

    def addMessage(self, message):
        self.queue.put(message)

    def getMessage(self):
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None