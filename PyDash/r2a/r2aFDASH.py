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

        self.bitrates = []
        self.time_request = 0
        self.rates = [46980, 91917, 135410, 182366, 226106, 270316, 352546, 424520, 537825, 620705, 808057, 1071529, 1312787, 1662809, 2234145, 2617284, 3305118, 3841983, 4242923, 4726737]
        self.previous_qi = 0
        self.next_qi = 0

        self.iterator = 0
        self.T = 5
        self.short = 0
        self.close = 0
        self.longg = 0
        self.differential = 0
        self.falling = 0
        self.steady = 0
        self.rising = 0
        self.p2 = 0
        self.p1 = 0
        self.z  = 0
        self.n1 = 0
        self.n2 = 0
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
        self.time_request = perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        time_download = perf_counter() - self.time_request
        self.bitrates.append(msg.get_bit_length() / time_download)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # time to define the segment quality choose to make the request

        # zerar as variaveis para novo ciclo
        self.short = 0
        self.close = 0
        self.longg = 0
        self.falling = 0
        self.steady = 0
        self.rising = 0
        self.p2 = 0
        self.p1 = 0
        self.z  = 0
        self.n1 = 0
        self.n2 = 0

        self.currDt = self.get_buffer_estimate()
        print(f"currDt: {self.currDt}")

        # fuzzification para definir variaveis short, close e long
        if self.currDt < 2*self.T/3:
            self.short = 1
        elif self.currDt >= 2*self.T/3 and self.currDt < self.T:
            self.short = 1 - (1/(self.T/3)*(self.currDt - (2*self.T/3)))
            self.close = (1/(self.T/3)) * (self.currDt-(2*self.T/3))
        elif self.currDt >= self.T and self.currDt < 4*self.T:
            self.close = 1-1/(3*self.T)*(self.currDt-self.T)
            self.longg = 1/(3*self.T)*(self.currDt-self.T)
        else:
            self.longg = 1

        print("short: " + str(self.short))
        print("close: " + str(self.close))
        print("long: " + str(self.longg))

        # define differential buffering time
        self.differential = self.get_buffer_differential()
        print(f"differential: {self.differential}")
        # fuzzification para definir variaveis falling, steady e rising

        if self.differential < -2*self.T/3:
            self.falling = 1
        elif self.differential >= -2*self.T/3 and self.differential < 0:
            self.falling = 1-(1/(2*self.T / 3)*(self.differential+2*self.T/3))
            self.steady = 1/(2*self.T/3)*(self.differential+2*self.T/3)
        elif self.differential < 4*self.T:
            self.steady = 1-(1/(4*self.T)*self.differential)
            self.rising = 1/(4*self.T)*self.differential
        else:
            self.rising = 1

        print("falling: " + str(self.falling))
        print("steady: " + str(self.steady))
        print("rising: " + str(self.rising))

        self.r1 = min(self.short, self.falling)
        self.r2 = min(self.close, self.falling)
        self.r3 = min(self.longg, self.falling)
        self.r4 = min(self.short, self.steady)
        self.r5 = min(self.close, self.steady)
        self.r6 = min(self.longg, self.steady)
        self.r7 = min(self.short, self.rising)
        self.r8 = min(self.close, self.rising)
        self.r9 = min(self.longg, self.rising)

        self.p2 = sqrt((self.r9 * self.r9))
        self.p1 = sqrt((self.r6 * self.r6) + (self.r8 * self.r8))
        self.z  = sqrt((self.r3 * self.r3) + (self.r5 * self.r5) + (self.r7 * self.r7))
        self.n1 = sqrt((self.r2 * self.r2) + (self.r4 * self.r4))
        self.n2 = sqrt((self.r1 * self.r1))

        output = (self.n2 * 0.25 + self.n1 * 0.5 + self.z * 1 + self.p1 * 1.5 + self.p2 * 2) / (self.n2 + self.n1 + self.z + self.p1 + self.p2)

        print(f"short = {self.short}, close = {self.close}, falling = {self.falling}, rising = {self.rising}," +
        f" steady = {self.steady}, r1 = {self.r1}, r2 = {self.r2}, r3 = {self.r3}, r4 = {self.r4}," + 
        f" r5 = {self.r5}, r6 = {self.r6}, r7 = {self.r7}, r8 = {self.r8}, r9 = {self.r9}, p2 = {self.p2}," +
        f" p1 = {self.p1}, z = {self.z}, n1 = {self.n1}, n2 = {self.n2}")

        bitrate_estimate = sum(self.bitrates)/len(self.bitrates)
        interruption_limit = 4726737

        result = output * bitrate_estimate

        if (result > interruption_limit):
            result = interruption_limit

        self.next_qi = 0

        for i in range(len(self.rates)):
            if result > self.rates[i]:
                self.next_qi = i

        if self.next_qi > self.previous_qi:
            t_60 = self.currDt + (bitrate_estimate / self.rates[self.next_qi] - 1) * 60

            if t_60 < self.T:
                self.next_qi = self.previous_qi

        elif self.next_qi < self.previous_qi and interruption_limit == self.rates[-1]:
            t_60 = self.currDt + (bitrate_estimate / self.rates[self.next_qi] - 1) * 60

            if t_60 > self.T:
                t_60 = self.currDt + (bitrate_estimate / self.rates[self.previous_qi] - 1) * 60
                
                if t_60 > self.T:
                    self.next_qi = self.previous_qi

        self.previous_qi = self.next_qi

        msg.add_quality_id(self.qi[self.next_qi])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

    def get_buffer_estimate(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if len(pssab) == 0:
            return 0

        soma = 0

        for element in pssab:
            soma += float(element)

        return soma/len(pssab)

    def get_buffer_differential(self):
        pssab = list(self.whiteboard.get_playback_segment_size_time_at_buffer())

        if (len(pssab) < 2):
            return 0

        return float(pssab[-1] - pssab[-2])
