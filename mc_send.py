#!/usr/bin/python

from __future__ import print_function
import socket
import time
import datetime
import argparse
import json
import os
import sys
import base64


def get_args():
    parser = argparse.ArgumentParser(description='Test Multicast Stream')
    parser.add_argument('group', help='Multicast Group Address')
    parser.add_argument('-p', '--port', help="UDP Port Number", default=5000, type=int)
    parser.add_argument('-t', '--ttl', help="Time To Live (Hops)", default=32, type=int)
    parser.add_argument('-f', '--freq', help="Packets Per Second", default=1, type=int)
    parser.add_argument('--pad', help="Number of characters to pad", default=50, type=int)
    return parser.parse_args()


def poll_loop(counter, mcast_grp, mcast_port, ttl, padding):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    padding = base64.b64encode(os.urandom(padding)).decode('utf-8')[:padding]
    now = time.time()
    data = json.dumps([counter, now, padding])
    sock.sendto(data.encode('utf-8'), (mcast_grp, mcast_port))
    print(data, end='\r')
    sys.stdout.flush()


def main():
    args = get_args()
    counter = 0
    while True:
        try:
            poll_loop(counter, args.group, args.port, args.ttl, args.pad)
            counter +=1
            time.sleep(1/args.freq)
        except KeyboardInterrupt:
            print("\n\nExited\n")
            exit()


if __name__ == "__main__":
    main()
