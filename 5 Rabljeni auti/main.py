import os
import argparse
import index, neostar, dasweltauto, trcz, autohrvatska, autoto

# preventivno čistim sve instance, pogotovo za vrijeme testiranja
def ocisti():
    os.system('taskkill /im chrome.exe /f')
    os.system('taskkill /im chromedriver.exe /f')

# definiranje argumenata za poziv iz komandne linije
def args():
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-w', '--workers', type=int, default=6, help='broj radnika u poolu')
    argParser.add_argument('-t', '--time_sleep', type=float, default=1, help='pauza između dohvata podataka')
    args = argParser.parse_args()
    return args.workers, args.time_sleep

if __name__ == '__main__':
    workers, time_sleep = args()
    ocisti()
    index.oglasi(workers, time_sleep)
    ocisti()
    neostar.oglasi(workers, time_sleep)
    ocisti()
    dasweltauto.oglasi(workers, time_sleep)
    ocisti()
    trcz.oglasi(workers, time_sleep)
    ocisti()
    autohrvatska.oglasi(workers, time_sleep)
    ocisti()
    autoto.oglasi(workers, time_sleep)
    ocisti()
