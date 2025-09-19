from threading import Thread, Lock, Event
from time import sleep
import random

from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode

from BroadcastMessage import BroadcastMessage
from MessageTo import MessageTo
from Mailbox import Mailbox
from Token import Token
from Status import Status
from SyncedMessageTo import SyncedMessageTo
from SyncAck import SyncAck
from BroadcastSyncMessage import BroadcastSyncMessage
from Synchronized import Synchronized
from NumberBroadcast import NumberBroadcast


class Com(Thread):
    """
    Classe de communication pour un processus distribué.
    Gère les messages synchrones/asynchrones, les tokens et la synchronisation
    entre processus dans un système distribué.
    """
    
    def __init__(self, process):
        """
        Initialise le composant de communication.
        
        Args:
            process: Le processus parent associé à cette instance de communication
        """
        super().__init__()

        # Configuration de base
        self.process = process
        self.mailbox = Mailbox()
        self.alive = True

        # Identification
        self.number = 0
        self.numbersArray = []
        self.nbProcess = 0
        self.name = "P?"
        self.process.name = self.name
        
        # Gestion de l'horloge logique
        self.clock = 0
        self.clock_lock = Lock()
        
        # États et synchronisation
        self.status = Status.NULL
        self.sc_event = Event()           # Section critique
        self.ack_event = Event()          # Accusés de réception
        self.sync_recv_event = Event()    # Réception synchrone
        self.sync_all_event = Event()     # Synchronisation globale
        
        # Messages et compteurs
        self.sync_msg = None
        self.count_ack = 0
        self.synchronized_count = 0
        
        # Enregistrement aux événements et démarrage du thread
        PyBus.Instance().register(self, self)
        self.start()

    # ==================== GESTION DE L'HORLOGE LOGIQUE ====================
    
    def inc_clock(self, other_clock=None):
        """
        Incrémente l'horloge logique selon l'algorithme de Lamport.
        
        Args:
            other_clock (int, optional): Horloge d'un autre processus pour synchronisation
        """
        with self.clock_lock:
            if other_clock is not None:
                self.clock = max(self.clock, other_clock) + 1
            else:
                self.clock += 1

    # ==================== RÉCEPTION D'ÉVÉNEMENTS ====================
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastMessage)
    def onBroadcastMessage(self, event):
        """
        Gère la réception d'un message de diffusion.
        
        Args:
            event (BroadcastMessage): Message de diffusion reçu
        """
        if event.getSender() != self.myId:
            self.mailbox.addMessage(event)
            self.inc_clock(event.getClock())

    @subscribe(threadMode=Mode.PARALLEL, onEvent=MessageTo)
    def onReceive(self, event):
        """
        Gère la réception d'un message point-à-point.
        
        Args:
            event (MessageTo): Message point-à-point reçu
        """
        if event.getTo() == self.myId:
            self.mailbox.addMessage(event)
            self.inc_clock(event.getClock())
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=Token)
    def onTokenReceived(self, event):
        """
        Gère la réception d'un token pour l'exclusion mutuelle.
        
        Args:
            event (Token): Token reçu
        """
        if event.getTo() == self.myId:
            self.mailbox.addMessage(event)
            
            if self.status == Status.REQUEST:
                self.status = Status.SC
                print(f"{self.name} entering SC")
                self.sc_event.set()
            else:
                self.sendToken()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncedMessageTo)
    def onSyncedMessageReceived(self, event):
        """
        Gère la réception d'un message synchrone point-à-point.
        
        Args:
            event (SyncedMessageTo): Message synchrone reçu
        """
        if event.getTo() == self.myId:
            self.sync_msg = event
            self.inc_clock(event.getClock())
            self.sync_recv_event.set()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=BroadcastSyncMessage)
    def onBroadcastSyncedReceived(self, event):
        """
        Gère la réception d'un message de diffusion synchrone.
        
        Args:
            event (BroadcastSyncMessage): Message de diffusion synchrone reçu
        """
        if event.getSender() != self.myId:
            self.sync_msg = event
            self.inc_clock(event.getClock())
            self.sync_recv_event.set()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=SyncAck)
    def onAckReceived(self, event):
        """
        Gère la réception d'un accusé de réception.
        
        Args:
            event (SyncAck): Accusé de réception reçu
        """
        if event.getTo() == self.myId:
            self.count_ack -= 1
            if self.count_ack == 0:
                self.ack_event.set()

    @subscribe(threadMode=Mode.PARALLEL, onEvent=Synchronized)
    def onSynchronizedReceived(self, event):
        """
        Reçoit les messages de synchronisation des autres processus.
        Libère la barrière quand tous sont arrivés (nbProcessCreated - 1).
        
        Args:
            event (Synchronized): Message de synchronisation reçu
        """
        if event.getSender() != self.myId:
            self.synchronized_count += 1
            if(self.synchronized_count == self.nbProcess - 1):
                self.sync_all_event.set()
    
    @subscribe(threadMode=Mode.PARALLEL, onEvent=NumberBroadcast)
    def onNumberBroadcast(self, event):
        """
        Reçoit les numéros des autres processus et met à jour les IDs.
        
        Args:
            event (NumberBroadcast): Message contenant le numéro d'un processus
        """
        if event.getNumber() != self.number:
            self.updateIds(event.getNumber())

    # ==================== ENVOI DE MESSAGES ====================

    def broadcast(self, message):
        """
        Diffuse un message à tous les processus.
        
        Args:
            message (str): Message à diffuser
        """
        self.inc_clock()
        m = BroadcastMessage(message, self.myId, self.clock)
        print(f"{self.name} broadcast: {m.getValue()}")
        PyBus.Instance().post(m)

    def sendTo(self, to, message):
        """
        Envoie un message point-à-point de manière asynchrone.
        
        Args:
            to (int): ID du processus destinataire
            message (str): Message à envoyer
        """
        self.inc_clock()
        m = MessageTo(message, self.myId, to, self.clock)
        print(f"{self.name} send: {m.getValue()}")
        PyBus.Instance().post(m)

    def sendToSync(self, to, message):
        """
        Envoie un message point-à-point de manière synchrone.
        Bloque jusqu'à réception de l'accusé de réception.
        
        Args:
            to (int): ID du processus destinataire
            message (str): Message à envoyer
        """
        self.inc_clock()
        m = SyncedMessageTo(message, self.name, to, self.clock)
        print(f"{self.name} send sync: {m.getValue()}")
        
        PyBus.Instance().post(m)
        self.count_ack = 1
        self.ack_event.wait()

    def broadcastSync(self, message, from_id):
        """
        Diffuse un message synchrone à tous les processus.
        
        Args:
            message (str): Message à diffuser
            from_id (int): ID du processus initiateur
        """
        if from_id != self.myId:
            return self.receiveFromSync(from_id)
        else:
            self.inc_clock()
            m = BroadcastSyncMessage(message, self.myId, self.clock)
            print(f"{self.name} broadcast sync: {m.getValue()}")
            
            self.count_ack = self.nbProcess - 1
            PyBus.Instance().post(m)
            
            if self.count_ack > 0:
                self.ack_event.wait()

    # ==================== GESTION DES TOKENS ====================

    def sendToken(self):
        """
        Envoie le token au processus suivant dans l'anneau.
        """
        if not self.process.alive:
            return
        to = (self.myId + 1) % (self.nbProcess - 1)
        token = Token(to)
        print(f"{self.name} send token to: {to}")
        sleep(1)
        PyBus.Instance().post(token)

    def requestSC(self):
        """
        Demande l'accès à la section critique.
        Bloque jusqu'à obtention du token.
        """
        self.status = Status.REQUEST
        print(f"{self.name} requests SC")
        self.sc_event.wait()

    def releaseSC(self):
        """
        Libère la section critique et transmet le token.
        """
        self.status = Status.NULL
        print(f"{self.name} released SC")
        self.sendToken()

    # ==================== RECEPTION SYNCHRONE ====================

    def receiveFromSync(self, from_id):
        """
        Attend et reçoit un message synchrone, puis envoie un accusé de réception.
        
        Args:
            from_id (int): ID du processus expéditeur
            
        Returns:
            Message reçu
        """
        if self.sync_msg is None:
            self.sync_recv_event.wait()
        
        self.inc_clock()
        msg = self.sync_msg
        self.sync_msg = None
        self.sync_recv_event.clear()
        self.sendAck(from_id)
        
        return msg
    
    def sendAck(self, to):
        """
        Envoie l'accusé de réception
        
        Args:
            to (int): ID du processus destinataire de l'ACK
        """
        ack = SyncAck(to)
        PyBus.Instance().post(ack)

    # ==================== SYNCHRONIZATION ====================

    def synchronize(self):
        """
        Barrière de synchronisation : bloque jusqu'à ce que tous les processus 
        atteignent ce point. Le dernier arrivé libère tous les autres.
        """
        self.sendSynchronized()
        if self.synchronized_count == self.nbProcess - 1:
            self.synchronized_count = 0
        else:
            print(f"{self.name} waiting for sync ...")
            self.sync_all_event.wait()
            self.synchronized_count = 0
            print(f"{self.name} freed from sync waiting")

    def sendSynchronized(self):
        """
        Diffuse un message de synchronisation à tous les processus 
        pour signaler l'arrivée à la barrière.
        """
        m = Synchronized(self.myId)
        print(f"{self.name} sent synchronized")
        PyBus.Instance().post(m)

    # ==================== NUMEROTATION ====================*

    def init(self):
        """
        Initialise la numérotation automatique des processus.
        Génère un numéro aléatoire et le diffuse à tous les processus.
        """
        self.number = random.randint(1, 10**10)
        self.numbersArray.append(self.number)
        m = NumberBroadcast(self.number)
        sleep(0.5) # Attente que tous les processus soient prêts
        PyBus.Instance().post(m)

    def updateIds(self, newNumber):
        """
        Met à jour les identifiants des processus basé sur le tri des numéros.
        
        Args:
            newNumber (int): Nouveau numéro reçu d'un autre processus
        """
        self.numbersArray.append(newNumber)
        self.numbersArray.sort()
        self.myId = self.numbersArray.index(self.number)
        self.name = "P" + str(self.myId)
        self.process.name = self.name
        self.nbProcess = len(self.numbersArray)
