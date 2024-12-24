from types import NoneType
from typing import List, TypeAlias, Union, Self
from enum import StrEnum

class OscValueOutOfRange(Exception): ...
class OscInvalidArgument(Exception): ...
class OscParseError(Exception): ...


class OSC_MIDIPacket(tuple):
  def __new__(cls, midi_msg: tuple[int,int,int,int] = (0,0,0,0), /) -> Self:
    return super().__new__(cls, midi_msg)


class OSC_RGBAPacket(tuple):
  def __new__(cls, rgba_tuple: tuple[int,int,int,int] = (0,0,0,0), /) -> Self:
    return super().__new__(cls, rgba_tuple)


OscArgsType: TypeAlias = Union[float, int, str, bytes, OSC_RGBAPacket, OSC_MIDIPacket, bool, NoneType]
OscList: TypeAlias = List[OscArgsType]
OscNestAbleList: TypeAlias = List[Union[OscArgsType, OscList]]


class OscTypesEnum(StrEnum):
  FLOAT32 = "f"
  FLOAT64 = "d"
  INT32 = "i"
  INT64 = "h"
  STRING = "s"
  BLOB = "b"
  RGBA32 = "r"
  MIDI = "m"

  OSC_TRUE = "T"
  OSC_FALSE = "F"
  OSC_NIL = "N"
  OSC_INF = "I"
  OSC_TIME = "t"
  ANY = "any"
  NOT_SUBPORTED_TYPE = "not supported"


_ARRAY_START = "["
_ARRAY_END = "]"

# osc types bytes lenght
_FLOAT32_DGRAM_LEN: int = 4
_FLOAT64_DGRAM_LEN: int = 8
_INT32_DGRAM_LEN: int = 4
_INT64_DGRAM_LEN: int = 8
_OSC_TIME_DGRAM_LEN: int = 8
_RGBA32_LEN: int = 4
_MIDI_LEN: int = 4

_STRING_DGRAM_PAD: int = 4
_BLOB_DGRAM_PAD: int = 4
