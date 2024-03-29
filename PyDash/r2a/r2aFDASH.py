# -*- coding: utf-8 -*-
"""
@author: Bruno M. O. de Castro 160069742@aluno.unb.br
@author: Leonardo T. Alves 160012007@aluno.unb.br
@author: Matheus R. B. Vieira 170062023@aluno.unb.br

@date: 14/10/2021

@description: PyDash Project

An implementation of an FDASH Algorithm (based on https://github.com/djvergad/dash)

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
        self.bitrates = []
        self.request_time = 0

        #max value of rates
        self.interruption_limit = 0

        #keeping selected QI
        self.previous_qi = 0
        self.next_qi = 0

        #algorithm's variables
        self.d = 30
        self.T = 60
        self.deltaT = 0

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
        self.bitrates.append(msg.get_bit_length() / time_download)

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

        self.current_ti = self.get_ti_estimate()

        # fuzzification para definir variaveis short, close e long
        if self.current_ti < 2 * self.T / 3:
            self.short = 1
        elif self.current_ti < self.T:
            self.short = 1 - (1 / (self.T / 3)) * (self.current_ti - (2 * self.T / 3))
            self.close = 1 - self.short
        elif self.current_ti < 4 * self.T:
            self.close = 1 - 1 / (3 * self.T) * (self.current_ti - self.T)
            self.longg = 1 - self.close
        else:
            self.longg = 1

        # define differential buffering time
        self.deltaT = self.get_current_deltaT()

        # fuzzification para definir variaveis falling, steady e rising
        if self.deltaT < -2 * self.T / 3:
            self.falling = 1
        elif self.deltaT < 0:
            self.falling = 1 - (1 / (2 * self.T / 3)) * (self.deltaT + 2 * self.T / 3)
            self.steady = 1 - self.falling
        elif self.deltaT < 4 * self.T:
            self.steady = 1 - (1 / (4 * self.T) * self.deltaT)
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

        bitrateEstimate = sum(self.bitrates)/len(self.bitrates)

        result = output * bitrateEstimate

        if (result > self.interruption_limit):
            result = self.interruption_limit

        self.next_qi = 0

        for i in range(len(self.qi)):
            if result > self.qi[i]:
                self.next_qi = i

        if self.next_qi > self.previous_qi:
            t_buffer_last_60 = self.current_ti + (bitrateEstimate / self.qi[self.next_qi] - 1) * 60

            if t_buffer_last_60 < self.T:
                self.next_qi = self.previous_qi

        elif self.next_qi < self.previous_qi and self.interruption_limit == self.qi[-1]:
            t_buffer_last_60 = self.current_ti + (bitrateEstimate / self.qi[self.next_qi] - 1) * 60

            if t_buffer_last_60 > self.T:
                t_buffer_last_60 = self.current_ti + (bitrateEstimate / self.qi[self.previous_qi] - 1) * 60
                
                if t_buffer_last_60 > self.T:
                    self.next_qi = self.previous_qi

        self.previous_qi = self.next_qi

        msg.add_quality_id(self.qi[self.next_qi])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        
        download_time = perf_counter() - self.request_time
        self.bitrates.append(msg.get_bit_length() / download_time)
        if len(self.bitrates) > self.d:
            self.bitrates = self.bitrates[-self.d:] #keep only last d values
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    def get_ti_estimate(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if len(pssab) == 0:
            return 0

        return sum(pssab)/len(pssab)

    def get_current_deltaT(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if (len(pssab) < 2):
            return 0

        return float(pssab[-1] - pssab[-2])
