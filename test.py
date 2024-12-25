import unittest
import math
from scr import *


class OscLibTest(unittest.TestCase):
  def constructOscMsg(self) -> None:
    test_1: OscMsg = OscMsg(
      "/VMC/status/OK",
      1,
      3.141592653579,
      "it__work",
      b'\x00hello\x00',
      OSC_RGBAPacket((255,255,255,255)),
      OSC_MIDIPacket((255,255,255,255)),
      True,
      False,
      None,
      math.inf,
      [ # pls work
        1,
        3.141592653579,
        "it__work",
        b'\x00hello\x00',
        OSC_RGBAPacket((255,255,255,255)),
        OSC_MIDIPacket((255,255,255,255)),
        True,
        False,
        None,
        math.inf,
      ]
      )



if __name__ == "__main__":
  unittest.main()
