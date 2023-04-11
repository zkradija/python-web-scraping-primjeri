import argparse
import index, neostar, dasweltauto, trcz, autohrvatska, autoto

def args():
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-w', '--workers', type=int, default=20, help='broj radnika u poolu')
    argParser.add_argument('-t', '--time_sleep', type=float, default=0.10, help='pauza između dohvata podataka')
    args = argParser.parse_args()
    return args.workers, args.time_sleep

if __name__ == '__main__':
    workers, time_sleep = args()
    index.oglasi(workers, time_sleep)
    neostar.oglasi(workers, time_sleep)
    dasweltauto.oglasi(workers, time_sleep)
    trcz.oglasi(workers, time_sleep)
    autohrvatska.oglasi(workers, time_sleep)
    autoto.oglasi(workers, time_sleep)
