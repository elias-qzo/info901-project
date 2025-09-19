from threading import Thread
from time import sleep
import random

from Com import Com
from Token import Token
from BroadcastMessage import BroadcastMessage
from MessageTo import MessageTo
from SyncedMessageTo import SyncedMessageTo
from Status import Status


class Process(Thread):
    """
    Classe représentant un processus dans un système distribué.
    Chaque processus possède son propre composant de communication et
    peut échanger des messages avec les autres processus.
    """
    
    def __init__(self):
        """
        Initialise un nouveau processus.
        
        Args:
            name (str): Nom du processus
            nbProcess (int): Nombre total de processus dans le système
        """
        super().__init__()
        
        self.alive = True
        self.com = Com(self)
        self.start()

    def run(self):
        """
        Boucle principale d'exécution du processus.
        Traite les messages reçus et exécute la logique métier.
        """
        loop = 0

        self.com.init()  # Initialisation (numérotation)
        
        # TOKEN (nécessaire pour SC)
        # if self.com.myId == self.com.nbProcess - 1:
        #     self.com.sendToken()

        while self.alive:
            print(f"{self.com.name} Loop: {loop}")
            self.unpackMessages()
            sleep(0.3)

            # ==================== EXEMPLES D'UTILISATION ====================

            # MESSAGE ASYNCHRONE
            # if self.com.myId == 0:
            #     self.com.sendTo(1, f"Hello P1, from {self.name}")

            # BROADCAST ASYNCHRONE
            # if self.com.myId == 0:
            #     self.com.broadcast("Hello everyone!")
            
            # MESSAGE SYNCHRONE
            # if self.com.myId == 0 and loop == 0:
            #     self.com.sendToSync(1, f"Hello P1, from {self.name}")
            # elif self.com.myId == 1:
            #     sleep(2)
            #     msg = self.com.receiveFromSync(1)
            #     print(msg.getValue())

            # BROADCAST SYNCHRONE
            # if loop == 0:
            #     msg = self.com.broadcastSync("Hello from broadcast sync", 0)
            #     if msg != None:
            #         print(self.com.name," ",msg.getValue())

            # SECTION CRITIQUE
            # if self.com.myId == 3:
            #     self.com.requestSC()
            #     print(f"{self.name} processing SC")
            #     sleep(3)
            #     self.com.releaseSC()

            # SYNCHRONIZE
            # if loop == 0:
            #     if self.com.myId == 2:
            #         sleep(4)
            #     self.com.synchronize()
            
            loop += 1
            
        print(f"{self.name} stopped")

    def unpackMessages(self):
        """
        Dépile et traite tous les messages asynchrones présents dans la mailbox.
        """
        msg = self.com.mailbox.getMessage()
        
        while msg:
            match msg:
                case MessageTo():
                    print(f"{self.com.name} received message from {msg.getSender()}: {msg.getValue()}")
                    
                case BroadcastMessage():
                    print(f"{self.com.name} received broadcast from {msg.getSender()}: {msg.getValue()}")
                    
            msg = self.com.mailbox.getMessage()

    def stop(self):
        self.alive = False
        self.join()