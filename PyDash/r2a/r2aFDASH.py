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

class R2AFDASH(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []

        # FDASH Parameters
        self.N2 = 0.25
        self.N1 = 0.5
        self.Z = 1
        self.N2 = 1.5
        self.N2 = 2
        self.iterator = 0
        self.T = 5
        self.short = 0
        self.close = 0
        self.longg = 0
        self.differential = 0
        self.falling = 0
        self.steady = 0
        self.rising = 0
        self.previous_buffering_time = 0
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
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

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
        # captar buferring time atual e printar
        self.buffering_time = self.whiteboard.get_amount_video_to_play()
        print("buffering_time: "+str(self.buffering_time))

        print("previous buffering_time: "+str(self.previous_buffering_time))

        # fuzzification para definir variaveis short, close e long
        if self.buffering_time < 2*self.T/3:
            self.short = 1
        elif self.buffering_time >= 2*self.T/3 and self.buffering_time < self.T:
            self.short = 1 - (1/(self.T/3)*(self.buffering_time - (2*self.T/3)))
            self.close = (1/(self.T/3)) * (self.buffering_time-(2*self.T/3))
        elif self.buffering_time >= self.T and self.buffering_time < 4*self.T:
            self.close = 1-1/(3*self.T)*(self.buffering_time-self.T)
            self.longg = 1/(3*self.T)*(self.buffering_time-self.T)
        else:
            self.longg = 1

        print("short: " + str(self.short))
        print("close: " + str(self.close))
        print("long: " + str(self.longg))

        print("buffering_time: "+str(self.buffering_time))
        print("previous buffering_time: "+str(self.previous_buffering_time))
        # define differential buffering time
        self.differential = self.buffering_time - self.previous_buffering_time
        print("differential: "+str(self.differential))
        # fuzzification para definir variaveis falling, steady e rising

        #print("T: "+str(self.T))
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

        # captar buferring time anterior e printar após primeiro ciclo
        self.previous_buffering_time = self.buffering_time

        msg.add_quality_id(self.qi[1])
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
