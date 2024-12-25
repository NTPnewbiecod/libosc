from scr import *
import math



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


print(f"construct : \n\t{test_1.getDgram()}\n")


test_1_parse: OscMsgParser = OscMsgParser(test_1.getDgram())
print(f"addr : {test_1_parse.getAddr()}\nargs : {test_1_parse.getArgs()}")
