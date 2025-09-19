from SystemMessage import SystemMessage

class Token(SystemMessage):
    def __init__(self, to):
        super().__init__(to)