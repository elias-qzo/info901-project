from time import sleep
from Process import Process

def launch(nbProcess, runningTime=5):
    processes = []

    for i in range(nbProcess):
        processes = processes + [Process()]

    sleep(runningTime)

    for p in processes:
        p.stop()

if __name__ == '__main__':

    #bus = EventBus.getInstance()
    
    launch(nbProcess=5, runningTime=5)

    #bus.stop()
