#!/usr/bin/python

from __future__ import print_function
import socket
import struct
import argparse
import datetime
import time
import json
import sys


class Latency(object):
    def __init__(self):
        self._last_reading = None
        self._counter = 0
        self._sum_latency = 0
        self._high = None
        self._low = None

    @property
    def last_reading(self):
        return self._last_reading

    @last_reading.setter
    def last_reading(self, value):
        self._last_reading = value
        self._counter += 1
        self._sum_latency += value
        if self._high is None:
            self._high = value
        elif self._high < value:
            self._high = value
        if value > 0:
            if self._low is None:
                self._low = value
            elif self._low > value:
                self._low = value

    @property
    def low(self):
        return self._low

    @property
    def high(self):
        return self._high

    @property
    def average(self):
        if self._counter > 0:
            return float(self._sum_latency / self._counter)
        else:
            return float(0)


def get_args():
    parser = argparse.ArgumentParser(description='Test Multicast Stream')
    parser.add_argument('group', help='Multicast Group Address')
    parser.add_argument('-p', '--port', help="UDP Port Number", default=5000, type=int)
    parser.add_argument('-l', '--long', help="Long Format Output", action='store_true')
    return parser.parse_args()


def mc_listen(mc_group, mc_port):
    total_received = 0
    total_dropped = 0
    last_counter = 0
    data_flag = False
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(5)
            sock.bind(('', mc_port))
            mreq = struct.pack("4sl", socket.inet_aton(mc_group), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            data = json.loads(sock.recv(10240).decode('utf-8'))
            # last_counter = data[0]
            while True:
                data = json.loads(sock.recv(10240).decode('utf-8'))
                data_flag = True
                total_received += 1
                # get time difference between timestamp in packet and now
                latency.last_reading = compare_time(data[1])
                # Check if packet sequence is correct
                if data[0] == (last_counter+1):
                    print_result(data[0], data[1], total_received, total_dropped)
                else:
                    dropped = data[0] - last_counter
                    if dropped <= 0:
                        print('\nCounter Reset or out of order Packets')
                    else:
                        print('Missed {0} packets'.format(dropped))
                        total_dropped += dropped
                    print_result(data[0], data[1], total_received, total_dropped)
                last_counter = data[0]

        except socket.timeout:
            if args.long:
                print('No Data Recieved on {0}:{1} - {2}                                  '.format(args.group, args.port, time.ctime()))
            else:
                # only one new line per missing segment
                if data_flag:
                    print('')
                data_flag = False
                
                print('No Data Recieved on {0}:{1} - {2}                                  '.format(args.group, args.port, time.ctime()), end='\r')
                sys.stdout.flush()
        except KeyboardInterrupt:
            exiting(total_received, total_dropped)
            exit()


def print_result(counter, timestamp, received, dropped):
    human_time = time.asctime(time.gmtime(timestamp))
    if args.long:
        print('{0} - Last Timestamp:{1} - Recieved: {2} - Dropped: {3} - Latency: {4:.3f}s'.format(counter,
                                                                                         human_time,
                                                                                         received,
                                                                                         dropped,
                                                                                         latency.last_reading))
    else:
        print('{0} - Last Timestamp:{1} - Recieved: {2} - Dropped: {3} - Latency: {4:.3f}s'.format(counter,
                                                                                         human_time,
                                                                                         received,
                                                                                         dropped,
                                                                                         latency.last_reading),
              end='\r')
        sys.stdout.flush()


def compare_time(time_sent):
    # time_sent = time.mktime(time_received.timetuple())
    time_now = time.time()
    time_difference = time_now - time_sent
    # print(time_difference)
    # return latency in milliseconds
    return time_difference


def exiting(received, dropped):
    print('\n\nExiting.  \n\n'
          ' Recieved       : {0} Packets\n'
          ' Dropped        : {1} Packets\n'
          ' Latency Min    : {2:.3f}s\n'
          ' Latency Average: {3:.3f}s\n'
          ' Latency Max    : {4:.3f}s\n'
          ' Jitter         : {5:.3f}s\n'.format(received,
                                             dropped,
                                             latency.low,
                                             latency.average,
                                             latency.high,
                                             latency.high - latency.low))


def main():
    print('Latency is approximate and assumes accurate clock synchronisation')
    mc_listen(args.group, args.port)


if __name__ == '__main__':
    args = get_args()
    latency = Latency()
    main()
