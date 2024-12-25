import math
import struct
import ntplib
import time
from typing import Union, Self
import osclib.osc_types as osc_types

class OscMsg:
    def __init__(self, addr: str) -> None:
        self._addr: str = addr
        self._dgram: bytes
        self._args_type_list: list[str] = [","]
        self._args_dgram_list: list[bytes] = []


    def getDgram(self) -> bytes:
        self._assemble(self._addr)
        return self._dgram


    def addOscArg(self, value: Union[osc_types.OscArgsType, osc_types.OscList], arg_types: str = osc_types.AUTO_ANY):
        """
        add typed argument to this message.

        Args:
            - value: The corresponding value for the argument.
            - osc_types: A value in osc_type.* defined in this class,
                        if osc_type.AUTO_ANY then the type will be guessed.
        #NOTE: if you want to use 'nested List' keep 'osc_type' as 'osc_types.AUTO_ANY'
        #NOTE: python cannot don't distinguish FLOAT64 and FLOAT32.
        if needed to please supply 'osc_type' to 'addOscArg' method to cast the value to said supported OscType
        """
        if isinstance(value, list):
            if osc_types == osc_types.AUTO_ANY:
                self._args_type_list.append(osc_types._ARRAY_START)
                for val in value:
                    self.addOscArg(val) #type: ignore
                self._args_type_list.append(osc_types._ARRAY_END)
            else:
                self._args_type_list.append(osc_types._ARRAY_START)
                for val, val_type in zip(value, arg_types):
                    self.addOscArg(val, val_type)   #type: ignore
                self._args_type_list.append(osc_types._ARRAY_END)

        _args_types: str = arg_types
        if osc_types == osc_types.AUTO_ANY:
            _args_types = self._getOSCTypes(value)
        match _args_types:
            case osc_types.FLOAT32: self._appendFloat32(value)  #type: ignore
            case osc_types.FLOAT64: self._appendFloat64(value)  #type: ignore
            case osc_types.INT32: self._appendInt32(value)      #type: ignore
            case osc_types.INT64: self._appendInt64(value)      #type: ignore
            case osc_types.STRING: self._appendString(value)    #type: ignore
            case osc_types.BLOB: self._appendBytes(value)       #type: ignore
            case osc_types.OSC_TRUE: self._appendBool(True)     #type: ignore
            case osc_types.OSC_FALSE: self._appendBool(False)   #type: ignore
            case osc_types.OSC_NIL: self._appendNull()          #type: ignore
            case osc_types.OSC_INF: self._appendInf()           #type: ignore
            case osc_types.RGBA32: self._appendRGBA32(value)    #type: ignore
            case osc_types.MIDI: self._appendMIDI(value)        #type: ignore
            case _: raise ValueError(f" OSC_ArgsValue Value : {value} with Type : '{type(value)}' is not supported ")




    @staticmethod
    def _getOSCTypes(val: Union[osc_types.OscArgsType, osc_types.OscList]) -> str:
        if val is None:
            return osc_types.OSC_NIL
        if isinstance(val, str):
            return osc_types.STRING
        if isinstance(val, bytes):
            return osc_types.BLOB
        if val is True:
            return osc_types.OSC_TRUE
        if val is False:
            return osc_types.OSC_FALSE
        if isinstance(val, int):
            if val.bit_length() > 32:
                return osc_types.INT64
        else:
            return osc_types.INT32
        #NOTE: python do not have way to check for float64
        if isinstance(val, float):
            if math.isinf(val):
                return osc_types.OSC_INF
        else:
            return osc_types.FLOAT32
        if isinstance(val, osc_types.OSC_RGBAPacket):
            return osc_types.RGBA32
        if isinstance(val, osc_types.OSC_MIDIPacket):
            return osc_types.MIDI
        return osc_types.NOT_SUBPORTED_TYPE



    def _stringAddrToBytes(self, text: str) -> bytes:
        text_bytes: bytes = text.encode("utf-8")
        if (len(text_bytes) % osc_types._STRING_DGRAM_PAD) != 0:
            return text_bytes + bytes(osc_types._STRING_DGRAM_PAD - (len(text_bytes) % osc_types._STRING_DGRAM_PAD))
        else:
            return text_bytes + bytes(osc_types._STRING_DGRAM_PAD)

    def _appendFloat32(self, val: float) -> None:
        self._args_type_list.append(osc_types.FLOAT32)
        self._args_dgram_list.append(struct.pack(">f", val))


    def _appendFloat64(self, val: float) -> None:
        self._args_type_list.append(osc_types.FLOAT64)
        self._args_dgram_list.append(struct.pack(">d", val))


    def _appendInt32(self, val: int) -> None:
        self._args_type_list.append(osc_types.INT32)
        self._args_dgram_list.append(struct.pack(">i", val))


    def _appendInt64(self, val: int) -> None:
        self._args_type_list.append(osc_types.INT64)
        self._args_dgram_list.append(struct.pack(">q", val))


    def _appendString(self, text: str) -> None:
        text_bytes: bytes = text.encode("utf-8")
        if (len(text_bytes) % osc_types._STRING_DGRAM_PAD) != 0:
            text_bytes = b"".join([text_bytes, bytes(osc_types._STRING_DGRAM_PAD - (len(text_bytes) % osc_types._STRING_DGRAM_PAD))])
        else:
            text_bytes = b"".join([text_bytes, bytes(osc_types._STRING_DGRAM_PAD)])
        self._args_type_list.append(osc_types.STRING)
        self._args_dgram_list.append(text_bytes)


    def _appendBytes(self, blob: bytes) -> None:
        bytes_pack: bytes
        if (len(blob) % 4) != 0:
            bytes_pack = struct.pack(">i", len(blob)) + blob + bytes(osc_types._BLOB_DGRAM_PAD - (len(blob) % osc_types._BLOB_DGRAM_PAD))
        else:
            bytes_pack = blob
        self._args_type_list.append(osc_types.BLOB)
        self._args_dgram_list.append(bytes_pack)


    def _appendRGBA32(self, rgba: osc_types.OSC_RGBAPacket) -> None:
        if len(rgba) != 4:
            raise osc_types.OscInvalidArgument("RGBA Tuple do not contain exactly 4 element")
        for v in rgba:
            if v < 0 or v > 255:
                raise osc_types.OscValueOutOfRange("RGBA value out of range")
        _pack_val = sum((val & 0xFF) << 8 * (3 - i) for i, val in enumerate(rgba))
        self._args_type_list.append(osc_types.RGBA32)
        self._args_dgram_list.append(struct.pack(">I", _pack_val))


    def _appendMIDI(self, midi_packet: osc_types.OSC_MIDIPacket) -> None:
        if len(midi_packet) != 4:
            raise osc_types.OscInvalidArgument("MIDI Tuple do not contain exactly 4 element")
        for v in midi_packet:
            if v < 0 or v > 255:
                raise osc_types.OscValueOutOfRange("MIDI value out of range")
        _pack_val = sum((val & 0xFF) << 8 * (3 - i) for i, val in enumerate(midi_packet))
        self._args_type_list.append(osc_types.MIDI)
        self._args_dgram_list.append(struct.pack(">I", _pack_val))


    def _appendBool(self, val: bool) -> None:
        if val:
            self._args_type_list.append(osc_types.OSC_TRUE)
        else:
            self._args_type_list.append(osc_types.OSC_FALSE)


    def _appendNull(self) -> None:
        self._args_type_list.append(osc_types.OSC_NIL)


    def _appendInf(self) -> None:
        self._args_type_list.append(osc_types.OSC_INF)


    def _appendOSCTime(self, sys_timestamp: float):
        ntp_time: float = ntplib.system_to_ntp_time(sys_timestamp)
        self._args_type_list.append(osc_types.OSC_TIME)
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

