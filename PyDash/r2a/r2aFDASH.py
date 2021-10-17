# -*- coding: utf-8 -*-
"""
@author: Bruno M. O. de Castro 160069742@aluno.unb.br
@author: Leonardo T. Alves 160012007@aluno.unb.br
@author: Matheus R. B. Vieira 170062023@aluno.unb.br

@date: 14/10/2021

@description: PyDash Project

An implementation of an FDASH Algorithm

The quality list is obtained with the parameter of handle_xml_response()
method and the choice is made inside of handle_segment_size_request(),
before sending the message down.
"""

from player.parser import *
from r2a.ir2a import IR2A
from math import sqrt
from time import perf_counter

class R2AFDASH(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

        #variables for calculating throughput
        self.bitrate = 0
        self.request_time = 0

        #max value of rates
        self.interruption_limit = 0

        #keeping selected QI
        self.previous_qi = 0
        self.next_qi = 0

        self.T = 35
        self.differential = 0

        #buffering time linguistic variables
        self.short = 0
        self.close = 0
        self.longg = 0
        self.falling = 0
        self.steady = 0
        self.rising = 0

        #factors of the output membership functions
        self.p2 = 0
        self.p1 = 0
        self.z  = 0
        self.n1 = 0
        self.n2 = 0

        #variables for rules 1 through 9
        self.r1 = 0
        self.r2 = 0
        self.r3 = 0
        self.r4 = 0
        self.r5 = 0
        self.r6 = 0
        self.r7 = 0
        self.r8 = 0
        self.r9 = 0

    def handle_xml_request(self, msg):
        self.request_time = perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        self.interruption_limit = self.qi[-1]

        time_download = perf_counter() - self.request_time
        self.bitrate = (msg.get_bit_length() / time_download)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = perf_counter()

        # resetting variable for new segment
        self.short = 0
        self.close = 0
        self.longg = 0
        self.falling = 0
        self.steady = 0
        self.rising = 0

        self.currDt = self.get_buffer_estimate()
        print('\033[92m' + f"currDt: {self.currDt}" + '\033[0m')

        # fuzzification para definir variaveis short, close e long
        if self.currDt < 2 * self.T / 3:
            self.short = 1
        elif self.currDt < self.T:
            self.short = 1 - (1 / (self.T / 3)) * (self.currDt - (2 * self.T / 3))
            self.close = 1 - self.short
        elif self.currDt < 4 * self.T:
            self.close = 1 - 1 / (3 * self.T) * (self.currDt - self.T)
            self.longg = 1 - self.close
        else:
            self.longg = 1

        # define differential buffering time
        self.differential = self.get_buffer_differential()
        print('\033[92m' + f"differential: {self.differential}" + '\033[0m')

        # fuzzification para definir variaveis falling, steady e rising
        if self.differential < -2 * self.T / 3:
            self.falling = 1
        elif self.differential < 0:
            self.falling = 1 - (1 / (2 * self.T / 3)) * (self.differential + 2 * self.T / 3)
            self.steady = 1 - self.falling
        elif self.differential < 4 * self.T:
            self.steady = 1 - (1 / (4 * self.T) * self.differential)
            self.rising = 1 - self.steady
        else:
            self.rising = 1

        #values for rules
        self.r1 = min(self.short, self.falling)
        self.r2 = min(self.close, self.falling)
        self.r3 = min(self.longg, self.falling)
        self.r4 = min(self.short, self.steady)
        self.r5 = min(self.close, self.steady)
        self.r6 = min(self.longg, self.steady)
        self.r7 = min(self.short, self.rising)
        self.r8 = min(self.close, self.rising)
        self.r9 = min(self.longg, self.rising)

        #calculate linguistic variables
        self.p2 = sqrt((self.r9 * self.r9))
        self.p1 = sqrt((self.r6 * self.r6) + (self.r8 * self.r8))
        self.z  = sqrt((self.r3 * self.r3) + (self.r5 * self.r5) + (self.r7 * self.r7))
        self.n1 = sqrt((self.r2 * self.r2) + (self.r4 * self.r4))
        self.n2 = sqrt((self.r1 * self.r1))

        output = (self.n2 * 0.25 + self.n1 * 0.5 + self.z * 1 + self.p1 * 1.5 + self.p2 * 2) / (self.n2 + self.n1 + self.z + self.p1 + self.p2)

        print('\033[94m' + f"short = {self.short:.5f}, close = {self.close:.5f}, long = {self.longg:.5f} falling = {self.falling:.5f}," +
        f" steady = {self.steady:.5f}, rising = {self.rising:.5f}, r1 = {self.r1:.5f}, r2 = {self.r2:.5f}, r3 = {self.r3:.5f}, r4 = {self.r4:.5f}," + 
        f" r5 = {self.r5:.5f}, r6 = {self.r6:.5f}, r7 = {self.r7:.5f}, r8 = {self.r8:.5f}, r9 = {self.r9:.5f}, p2 = {self.p2:.5f}," +
        f" p1 = {self.p1:.5f}, z = {self.z:.5f}, n1 = {self.n1:.5f}, n2 = {self.n2:.5f}, output = {output:.5f}" + '\033[0m')

        print('\033[91m' + f"bitrate: {self.bitrate}" + '\033[0m')

        result = output * self.bitrate

        if (result > self.interruption_limit):
            result = self.interruption_limit

        self.next_qi = 0

        for i in range(len(self.qi)):
            if result > self.qi[i]:
                self.next_qi = i

        if self.next_qi > self.previous_qi:
            t_60 = self.currDt + (self.bitrate / self.qi[self.next_qi] - 1) * 60

            if t_60 < self.T:
                self.next_qi = self.previous_qi

        elif self.next_qi < self.previous_qi and self.interruption_limit == self.qi[-1]:
            t_60 = self.currDt + (self.bitrate / self.qi[self.next_qi] - 1) * 60

            if t_60 > self.T:
                t_60 = self.currDt + (self.bitrate / self.qi[self.previous_qi] - 1) * 60
                
                if t_60 > self.T:
                    self.next_qi = self.previous_qi

        self.previous_qi = self.next_qi

        msg.add_quality_id(self.qi[self.next_qi])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        
        download_time = perf_counter() - self.request_time
        self.bitrate = (msg.get_bit_length() / download_time)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    def get_buffer_estimate(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if len(pssab) == 0:
            return 0

        return sum(pssab)/len(pssab)

    def get_buffer_differential(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if (len(pssab) < 2):
            return 0

        return float(pssab[-1] - pssab[-2])
