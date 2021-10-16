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

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        # getting qi list
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        # Aqui vai o ABR
        slow = 0, ok = 0, fast = 0, falling = 0, steady = 0, rising = 0, r1 = 0, r2 = 0, r3 = 0,
        r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, p2 = 0, p1 = 0, z = 0, n1 = 0, n2 = 0,
        output = 0

        msg.add_quality_id(self.qi[1])

        self.send_down(msg)

    def handle_segment_size_response(self, msg):

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
