import os

import numpy as np

from atrcopy import DefaultSegment, SegmentData

from omnivore.arch.disasm import parse_jumpman_level, get_jumpman_level, parse_jumpman_harvest, get_jumpman_harvest
from omnivore.utils.jumpman import JumpmanLevelBuilder

class TestJumpmanLevel(object):
    def setup(self):
        self.items = [
            ([0xfe, 0x00, 0x04], 1),
            ([0xfc, 0x00, 0x40], 1),
            ([0xfd, 4, 9, 5], 1),
            ]

    def test_simple(self):
        for before, count in self.items:
            groups = parse_jumpman_level(before)
            for group in groups:
                text = get_jumpman_level(group)
                print "processed:", text
            print "groups", groups
            assert len(groups) == count

class TestJumpmanHarvest(object):
    def setup(self):
        self.items = [
            ([0x22, 0x04, 0x06, 0x4b, 0x28, 0x54, 0x2d], 1),
            ]

    def test_simple(self):
        for before, count in self.items:
            groups = parse_jumpman_harvest(before)
            for group in groups:
                text = get_jumpman_harvest(group)
                print "processed:", text
            print "groups", groups
            assert len(groups) == count

class TestJumpmanScreen(object):
    def setup(self):
        self.screen = np.zeros(40*90, dtype=np.uint8)
        data = np.fromstring("\x04\x00\x00\x01\x01\x01\x01\x04\x00\x01\x01\x00\x01\x00\x04\x00\x02\x01\x01\x01\x01\xff\x04\x00\x00\x00\x00\x00\x00\x04\x00\x01\x00\x00\x00\x00\x04\x00\x02\x00\x00\x00\x00\xff\x02\x00\x00\x02\x02\x02\x06\x00\x02\x02\x02\x00\x01\x02\x02\x02\x06\x01\x02\x02\x08\x00\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x00\x03\x02\x02\x02\x06\x03\x02\x02\xff\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\xff\x04\x00\x00\x00\x03\x03\x00\x04\x00\x01\x03\x00\x00\x03\x04\x00\x02\x00\x03\x03\x00\xff\x04\x00\x00\x00\x00\x00\x00\x04\x00\x01\x00\x00\x00\x00\x04\x00\x02\x00\x00\x00\x00\xff\x01\x00\x00\x01\x01\x01\x01\x01\x01\x00\x02\x01\x01\x01\x03\x01\xff\x01\x00\x00\x02\x01\x00\x01\x02\x01\x01\x02\x02\x01\x01\x03\x02\xff\x02\x00\x00\x00\x00\x02\x00\x01\x00\x00\x02\x00\x02\x00\x00\x02\x00\x03\x00\x00\xff", dtype=np.uint8)
        r = SegmentData(data)
        segments = [DefaultSegment(r, 0x4000)]
        self.builder = JumpmanLevelBuilder(segments)

    def test_simple(self):
        commands = [
            np.fromstring("\xfe\x04\x00\xfc\x00@\xfd\x04\t\x05\xfd$\t\x06\xfdd\t\x06\xfd\x88\t\x05\xfd(\x19\x04\xfdh\x19\x04\xfd\x04\x1d\x05\xfdD\x1d\x06\xfd\x88\x1d\x05\xfd\x04-\x05\xfd$-\x02\xfd8-\x0c\xfdt-\x02\xfd\x88-\x05\xfd8=\x0c\xfd\x04E\x06\xfd\x84E\x06\xfd\x04U&\xfdHR\x04\xfe\x04\xff\xfd\x18\n\x01\xfd|\n\x01\xfd\x1c\x0b\x02\xfd\x80\x0b\x02\xfd<\x08\x03\xfd\\\x1c\x03\xfd\x1cD\x07\xfe\x04\x01\xfdX\x06\x03\xfd8\x1a\x03\xfdh>\x07\xfe\x00\x04\xfc,@\xfd\x0c\x05\x0b\xfd\x0cA\x05\xfd,\x05\x05\xfd<)\x05\xfdL\x19\x05\xfd\\)\x05\xfdl\x05\x05\xfd\x8c\x05\x0b\xfd\x8cA\x05\xfc\xaf@\xfd'0\x02\xfdw0\x02\xfc\x83@\xfd\x04\x06\x01\xfdD\x03\x01\xfdX\x03\x01\xfd\x98\x06\x01\xfd\x04\x15\x01\xfd\x98\x15\x01\xfd$%\x01\xfdx%\x01\xfd\x04R\x01\xfd@G\x01\xfd\\G\x01\xfd\x98R\x01\xff", dtype=np.uint8),
        ]

        for c in commands:
            text_commands = self.builder.parse_commands(c)
            print "\n".join([str(a) for a in text_commands])
            self.builder.draw_commands(self.screen, c)

if __name__ == "__main__":
    t = TestJumpmanScreen()
    t.setup()
    t.test_simple()
