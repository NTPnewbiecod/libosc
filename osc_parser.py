import struct
from time import time
from typing import List, Any
import ntplib
from osc_types import (
  OSC_RGBAPacket,
  OSC_MIDIPacket,
  OscParseError,
  _FLOAT32_DGRAM_LEN,
  _FLOAT64_DGRAM_LEN,
  _INT32_DGRAM_LEN,
  _BLOB_DGRAM_PAD,
  _OSC_TIME_DGRAM_LEN

)





class OscMsgParser:
  def __init__(self, dgram: bytes) -> None:
    self._dgram: bytes = dgram
    self._next_start_idx: int = 0
    self.addr: str = ""
    self.args: list[Any] = []
    self._parse()


  def getAddr(self) -> str:
    return self.addr


  def getArgs(self) -> list[Any]:
    return self.args


  def _parse(self) -> None:
    self.addr = self._getAddr()
    args_types: str = self._getArgsTypes()
    for i in args_types:
      match i: # type: ignore
        case OscTypesEnum.FLOAT32.value: self.args.append(self._getFloat32()) #type: ignore
        case OscTypesEnum.FLOAT64.value: self.args.append(self._getFloat64()) #type: ignore
        case OscTypesEnum.INT32.value: self.args.append(self._getInt32())     #type: ignore
        case OscTypesEnum.INT64.value: self.args.append(self._getInt64())     #type: ignore
        case OscTypesEnum.STRING.value: self.args.append(self._getString())   #type: ignore
        case OscTypesEnum.BLOB.value: self.args.append(self._getBytes())      #type: ignore
        case OscTypesEnum.OSC_TRUE.value: self.args.append(True)              #type: ignore
        case OscTypesEnum.OSC_FALSE.value: self.args.append(False)            #type: ignore
        case OscTypesEnum.OSC_NIL.value: self.args.append(None)               #type: ignore
        case OscTypesEnum.OSC_INF.value: self.args.append(math.inf)           #type: ignore
        case OscTypesEnum.RGBA32.value: self.args.append(self._getRGBA())     #type: ignore
        case OscTypesEnum.MIDI.value: self.args.append(self._getMIDI())       #type: ignore
        case _: raise OscParseError("parse fail.")


  def _getAddr(self, max_str_len: int = 512) -> str:
    for i_len in range(4, max_str_len, 4):
      str_bytes: bytes = self._dgram[0 : i_len]
      #NOTE: A simgle b'\x00' is in fact equal to 0 but somehow not to b'\x00' in this situation
      if str_bytes[len(str_bytes) - 1] == 0:
        # remove padding and null terminater
        str_bytes = str_bytes.removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00')
        self._next_start_idx += i_len
        return str_bytes.decode("utf-8")
      else:
        continue
    raise OscParseError('fail to parse osc address')


  def _getArgsTypes(self, max_str_len: int = 512) -> str:
    idx = self._next_start_idx
    for i_len in range(4, max_str_len, 4):
      str_bytes: bytes = self._dgram[idx : idx + i_len]
      if str_bytes[len(str_bytes) - 1] == 0:
        # remove padding and null terminater
        str_bytes = str_bytes.removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00')
        # remove , that signafy start of typing str
        str_bytes = str_bytes.removeprefix(b',')
        self._next_start_idx += i_len
        return str_bytes.decode("utf-8")
      else:
        continue
    raise OscParseError('fail to parse osc string')


  def _getFloat32(self) -> int:
    idx = self._next_start_idx
    self._next_start_idx = idx + _FLOAT32_DGRAM_LEN
    return struct.unpack(">f", self._dgram[idx : idx + _FLOAT32_DGRAM_LEN])[0]


  def _getFloat64(self) -> int:
    idx = self._next_start_idx
    self._next_start_idx = idx + _FLOAT64_DGRAM_LEN
    return struct.unpack(">f", self._dgram[idx : idx + _FLOAT64_DGRAM_LEN])[0]


  def _getInt32(self) -> float:
    idx = self._next_start_idx
    self._next_start_idx = idx + _FLOAT32_DGRAM_LEN
    return struct.unpack(">i", self._dgram[idx : idx + _FLOAT32_DGRAM_LEN])[0]


  def _getInt64(self) -> float:
    idx = self._next_start_idx
    self._next_start_idx = idx + _FLOAT64_DGRAM_LEN
    return struct.unpack(">q", self._dgram[idx : idx + _FLOAT64_DGRAM_LEN])[0]


  def _getString(self, max_str_len: int = 512) -> str:
    idx = self._next_start_idx
    for i_len in range((max_str_len + 4) // 4):
      str_bytes: bytes = self._dgram[idx : idx + (4 * (i_len + 1))]
      if str_bytes[len(str_bytes) - 1] == 0:
        # remove padding and null terminater
        str_bytes = str_bytes.removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00').removesuffix(b'\x00')
        self._next_start_idx = idx + (4 * (i_len + 1))
        return str_bytes.decode("utf-8")
      else:
        continue
    raise OscParseError('fail to parse osc string')


  def _getBytes(self) -> bytes:
    idx = self._next_start_idx
    blob_len: int = struct.unpack(">i", self._dgram[idx : idx + _INT32_DGRAM_LEN])[0]
    self._next_start_idx = idx + _INT32_DGRAM_LEN + blob_len + (_BLOB_DGRAM_PAD - (blob_len % _BLOB_DGRAM_PAD))
    return self._dgram[idx + _INT32_DGRAM_LEN : idx + _INT32_DGRAM_LEN + blob_len]


  def _getRGBA(self) -> OSC_RGBAPacket:
    idx = self._next_start_idx
    pack_rgba: int = struct.unpack(">i", self._dgram[idx : idx + _INT32_DGRAM_LEN])[0]
    r_val: int = (pack_rgba & 0xFF000000) >> 8 * 3
    g_val: int = (pack_rgba & 0x00FF0000) >> 8 * 2
    b_val: int = (pack_rgba & 0x0000FF00) >> 8
    a_val: int = (pack_rgba & 0x000000FF)
    return OSC_RGBAPacket((r_val, g_val, b_val, a_val))


  def _getMIDI(self) -> OSC_MIDIPacket:
    idx = self._next_start_idx
    pack_rgba: int = struct.unpack(">i", self._dgram[idx : idx + _INT32_DGRAM_LEN])[0]
    r_val: int = (pack_rgba & 0xFF000000) >> 8 * 3
    g_val: int = (pack_rgba & 0x00FF0000) >> 8 * 2
    b_val: int = (pack_rgba & 0x0000FF00) >> 8
    a_val: int = (pack_rgba & 0x000000FF)
    return OSC_MIDIPacket((r_val, g_val, b_val, a_val))


  def _getOscTime(self) -> float:
    idx = self._next_start_idx
    self._next_start_idx = idx + _OSC_TIME_DGRAM_LEN
    time_pack: tuple[int, int] = struct.unpack(">II", self._dgram[idx : idx + _OSC_TIME_DGRAM_LEN])
    return ntplib.ntp_to_system_time(ntplib._to_time(time_pack[0], time_pack[1], 32))


class OscBundleParser:
  def __init__(self, dgram: bytes, max_element_to_parse: int = 256) -> None:
    if not dgram.startswith(b'#bundle\x00'):
      raise OscParseError(f"dgram does not start with b'#bundle\x00' but found {dgram[0 : 8]} instead.")
    self._dgram: bytes = dgram
    self.max_element_to_parse = max_element_to_parse
    self._next_start_idx: int = len(b'#bundle\x00')
    self.element: List[OscMsgParser | OscBundleParser] = []
    self.time_stamp: float = self._getTimeStamp()
    self._parse()

  def _getTimeStamp(self) -> float:
    idx = self._next_start_idx
    time_pack: tuple[int, int] = struct.unpack(">II", self._dgram[idx : idx + _OSC_TIME_DGRAM_LEN])
    self._next_start_idx += _OSC_TIME_DGRAM_LEN
    return ntplib.ntp_to_system_time(ntplib._to_time(time_pack[0], time_pack[1], 32))


  def _getBundleElement(self) -> None:
    idx = self._next_start_idx
    dgram_len: int = struct.unpack(">i", self._dgram[idx : idx + _INT32_DGRAM_LEN])[0]
    data_start_idx = idx + _INT32_DGRAM_LEN
    element_dgram: bytes = self._dgram[data_start_idx : data_start_idx + dgram_len]
    if element_dgram.startswith(b'#bundle\x00'):
      self.element.append(OscBundleParser(element_dgram))
    else:
      self.element.append(OscMsgParser(element_dgram))
    self._next_start_idx = data_start_idx + dgram_len


  def _parse(self) -> None:
    for i in range(self.max_element_to_parse):
      self._getBundleElement()
      if self._next_start_idx >= len(self._dgram):
        break

