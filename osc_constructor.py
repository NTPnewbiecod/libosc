import math
import struct
import ntplib
import time
from typing import Union, Self
from osc_types import (
  OscArgsType,
  OscInvalidArgument,
  OscList,
  OscNestAbleList,
  OscTypesEnum,
  OSC_MIDIPacket,
  OSC_RGBAPacket,
  _ARRAY_START,
  _ARRAY_END,
  _STRING_DGRAM_PAD,
  _BLOB_DGRAM_PAD,
  OscValueOutOfRange,
  OscInvalidArgument
)


class OscMsg:
  def __init__(self, addr: str, *argv: Union[OscArgsType, OscNestAbleList]) -> None:
    self._addr: str = addr
    self._dgram: bytes
    self._args_type_list: list[str] = [","]
    self._args_dgram_list: list[bytes] = []
    self.addOscArgs(*argv)


  def getDgram(self) -> bytes:
    self._assemble(self._addr)
    return self._dgram

  def addOscArgs(self, *argv: Union[OscArgsType, OscNestAbleList]) -> None:
    for value in argv:
      if isinstance(value, list):
        if value == []:
          raise ValueError("OSC_List is empty")
        self._args_type_list.append(_ARRAY_START)
        self.addOscArgs(value)
        self._args_type_list.append(_ARRAY_END)
      #check for real tuple and Exclude OSC_MIDIPacket and OSC_RGBAPacket
      elif isinstance(value, tuple) and (not isinstance(value, OSC_MIDIPacket)) and (not isinstance(value, OSC_RGBAPacket)):
        if len(value) == 0:
          raise ValueError("Tuple is empty")
        self._args_type_list.append(_ARRAY_START)
        self.addOscArgs(value)
        self._args_type_list.append(_ARRAY_END)
      else:
         self.addOscArg(value, self._getOSCTypes(value)) # type: ignore


  def addOscArg(self, value: OscArgsType, osc_type: OscTypesEnum):
    match osc_type: # type: ignore
      case OscTypesEnum.FLOAT32: self._appendFloat32(value) #type: ignore
      case OscTypesEnum.FLOAT64: self._appendFloat64(value) #type: ignore
      case OscTypesEnum.INT32: self._appendInt32(value)     #type: ignore
      case OscTypesEnum.INT64: self._appendInt64(value)     #type: ignore
      case OscTypesEnum.STRING: self._appendString(value)   #type: ignore
      case OscTypesEnum.BLOB: self._appendBytes(value)      #type: ignore
      case OscTypesEnum.OSC_TRUE: self._appendBool(True)    #type: ignore
      case OscTypesEnum.OSC_FALSE: self._appendBool(False)  #type: ignore
      case OscTypesEnum.OSC_NIL: self._appendNull()         #type: ignore
      case OscTypesEnum.OSC_INF: self._appendInf()          #type: ignore
      case OscTypesEnum.RGBA32: self._appendRGBA32(value)   #type: ignore
      case OscTypesEnum.MIDI: self._appendMIDI(value)       #type: ignore
      case _: raise ValueError(f" OSC_ArgsValue Value : {value} with Type : '{type(value)}' is not supported ")


  def addOscListArgs(self, listed_val: OscList, osc_type_chars: Union[list[str], str]):
    """
    OSC Type Char:
    FLOAT32 = "f"
    FLOAT64 = "d"
    INT32 = "i"
    INT64 = "h"
    STRING = "s"
    BLOB = "b"
    RGBA32 = "r"
    MIDI = "m"

    Note: below type will put in it said value even if it do not match value provided.
    OSC_TRUE = "T"
    OSC_FALSE = "F"
    OSC_NIL = "N"
    OSC_INF = "I"

    Example:
      OscMsg.addOscListArgs([1, 2.3, "asdf"], "ifs")
    """
    if isinstance(listed_val, list):
      if listed_val == []:
        raise ValueError("OSC_List is empty")
    if osc_type_chars == "" or osc_type_chars == []:
      raise ValueError("osc_type_chars is empty")
    if len(osc_type_chars) != len(listed_val):
        raise ValueError("OSC_List lenght do not match with osc_type_chars lenght")

    self._args_type_list.append(_ARRAY_START)
    for i, value in enumerate(listed_val):
      match osc_types[i]: # type: ignore
        case OscTypesEnum.FLOAT32.value: self._appendFloat32(value) #type: ignore
        case OscTypesEnum.FLOAT64.value: self._appendFloat64(value) #type: ignore
        case OscTypesEnum.INT32.value: self._appendInt32(value)     #type: ignore
        case OscTypesEnum.INT64.value: self._appendInt64(value)     #type: ignore
        case OscTypesEnum.STRING.value: self._appendString(value)   #type: ignore
        case OscTypesEnum.BLOB.value: self._appendBytes(value)      #type: ignore
        case OscTypesEnum.OSC_TRUE.value: self._appendBool(True)    #type: ignore
        case OscTypesEnum.OSC_FALSE.value: self._appendBool(False)  #type: ignore
        case OscTypesEnum.OSC_NIL.value: self._appendNull()         #type: ignore
        case OscTypesEnum.OSC_INF.value: self._appendInf()          #type: ignore
        case OscTypesEnum.RGBA32.value: self._appendRGBA32(value)   #type: ignore
        case OscTypesEnum.MIDI.value: self._appendMIDI(value)       #type: ignore
        case _: raise ValueError(f" OSC_ArgsValue Value : {value} with Type : '{type(value)}' char type : '{osc_type_chars[i]}' is not supported ")
    self._args_type_list.append(_ARRAY_END)


  @staticmethod
  def _getOSCTypes(val: OscArgsType) -> OscTypesEnum:
    """
    #NOTE: python cannot don't distinguish FLOAT64 and FLOAT32.
    if needed to please use 'addOscArg' method or 'addOscListArgs' method to cast the value to said supported OscType
    """

    if val is None: return OscTypesEnum.OSC_NIL
    if isinstance(val, str): return OscTypesEnum.STRING
    if isinstance(val, bytes): return OscTypesEnum.BLOB
    if val is True: return OscTypesEnum.OSC_TRUE
    if val is False: return OscTypesEnum.OSC_FALSE
    if isinstance(val, int):
      if val.bit_length() > 32:
        return OscTypesEnum.INT64
      else:
        return OscTypesEnum.INT32
    if isinstance(val, float):    #NOTE: python do not have way to check for float64
      if math.isinf(val):
        return OscTypesEnum.OSC_INF
      return OscTypesEnum.FLOAT32
    if isinstance(val, OSC_RGBAPacket): return OscTypesEnum.RGBA32
    if isinstance(val, OSC_MIDIPacket): return OscTypesEnum.MIDI
    return OscTypesEnum.NOT_SUBPORTED_TYPE



  def _stringAddrToBytes(self, text: str) -> bytes:
    text_bytes: bytes = text.encode("utf-8")
    if (len(text_bytes) % _STRING_DGRAM_PAD) != 0:
      return text_bytes + bytes(_STRING_DGRAM_PAD - (len(text_bytes) % _STRING_DGRAM_PAD))
    else:
      return text_bytes + bytes(_STRING_DGRAM_PAD)

  def _appendFloat32(self, val: float) -> None:
    self._args_type_list.append(OscTypesEnum.FLOAT32.value)
    self._args_dgram_list.append(struct.pack(">f", val))


  def _appendFloat64(self, val: float) -> None:
    self._args_type_list.append(OscTypesEnum.FLOAT64.value)
    self._args_dgram_list.append(struct.pack(">d", val))


  def _appendInt32(self, val: int) -> None:
    self._args_type_list.append(OscTypesEnum.INT32.value)
    self._args_dgram_list.append(struct.pack(">i", val))


  def _appendInt64(self, val: int) -> None:
    self._args_type_list.append(OscTypesEnum.INT64.value)
    self._args_dgram_list.append(struct.pack(">q", val))


  def _appendString(self, text: str) -> None:
    text_bytes: bytes = text.encode("utf-8")
    if (len(text_bytes) % _STRING_DGRAM_PAD) != 0:
      text_bytes = b"".join([text_bytes, bytes(_STRING_DGRAM_PAD - (len(text_bytes) % _STRING_DGRAM_PAD))])
    else:
      text_bytes = b"".join([text_bytes, bytes(_STRING_DGRAM_PAD)])
    self._args_type_list.append(OscTypesEnum.STRING.value)
    self._args_dgram_list.append(text_bytes)


  def _appendBytes(self, blob: bytes) -> None:
    bytes_pack: bytes
    if (len(blob) % 4) != 0:
      bytes_pack = b''.join([struct.pack(">i", len(blob)),
                             blob,
                             bytes(_BLOB_DGRAM_PAD - (len(blob) % _BLOB_DGRAM_PAD))])
    else:
      bytes_pack = blob
    self._args_type_list.append(OscTypesEnum.BLOB.value)
    self._args_dgram_list.append(bytes_pack)


  def _appendRGBA32(self, rgba: OSC_RGBAPacket) -> None:
    if len(rgba) != 4:
      raise OscInvalidArgument("RGBA Tuple do not contain exactly 4 element")
    for v in rgba:
      if v < 0 or v > 255:
        raise OscValueOutOfRange("RGBA value out of range")
    _pack_val = sum((val & 0xFF) << 8 * (3 - i) for i, val in enumerate(rgba))
    self._args_type_list.append(OscTypesEnum.RGBA32.value)
    self._args_dgram_list.append(struct.pack(">I", _pack_val))


  def _appendMIDI(self, midi_packet: OSC_MIDIPacket) -> None:
    if len(midi_packet) != 4:
      raise OscInvalidArgument("MIDI Tuple do not contain exactly 4 element")
    for v in midi_packet:
      if v < 0 or v > 255:
        raise OscValueOutOfRange("MIDI value out of range")
    _pack_val = sum((val & 0xFF) << 8 * (3 - i) for i, val in enumerate(midi_packet))
    self._args_type_list.append(OscTypesEnum.MIDI.value)
    self._args_dgram_list.append(struct.pack(">I", _pack_val))


  def _appendBool(self, val: bool) -> None:
    if val:
      self._args_type_list.append(OscTypesEnum.OSC_TRUE.value)
    else:
      self._args_type_list.append(OscTypesEnum.OSC_FALSE.value)


  def _appendNull(self) -> None:
    self._args_type_list.append(OscTypesEnum.OSC_NIL.value)


  def _appendInf(self) -> None:
    self._args_type_list.append(OscTypesEnum.OSC_INF.value)


  def _appendOSCTime(self, sys_timestamp: float):
    ntp_time: float = ntplib.system_to_ntp_time(sys_timestamp)
    self._args_type_list.append(OscTypesEnum.OSC_TIME.value)
    self._args_dgram_list.append(struct.pack(">II", ntplib._to_int(ntp_time), ntplib._to_frac(ntp_time)))


  def _assemble(self, addr: str):
    paded_args_types_list: list[bytes] = [s.encode("utf-8") for s in self._args_type_list]
    if (len(self._args_type_list) % 4) != 0:
      paded_args_types_list.append(bytes(4 - (len(self._args_type_list) % 4)))
    else:
      paded_args_types_list.append(bytes(4))
    self._dgram = b''.join([self._stringAddrToBytes(addr),
                            b''.join(paded_args_types_list),
                            b''.join(self._args_dgram_list)
                            ])



class OscBundle:
  def __init__(self, osc_element_list: list[OscMsg | Self], *, sys_timestamp: float = time.time()) -> None:
    ntp_time: float = ntplib.system_to_ntp_time(sys_timestamp)
    self._dgram: bytes = b'#bundle\x00' + struct.pack(">II", ntplib._to_int(ntp_time), ntplib._to_frac(ntp_time, 32))
    for osc_element in osc_element_list:
      msg_dgram: bytes = osc_element.getDgram()
      self._dgram += struct.pack(">i", len(msg_dgram)) + msg_dgram


  def getDgram(self):
    return self._dgram
