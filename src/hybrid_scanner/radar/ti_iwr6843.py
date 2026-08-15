from __future__ import annotations

import math
import struct
import time
from pathlib import Path

from loguru import logger

try:
    import serial
except ImportError:  # simulation/parser tests work without serial hardware dependency
    serial = None

from hybrid_scanner.models import RadarFrame, RadarPoint


MAGIC_WORD = b"\x02\x01\x04\x03\x06\x05\x08\x07"
HEADER_LEN_XWR68XX = 40
TLV_HEADER_LEN = 8
TLV_DETECTED_POINTS = 1
TLV_SIDE_INFO = 7


class TiPacketParser:
    """Defensive parser for the legacy xWR68xx mmWave demo UART packet.

    TI firmware families differ in output layouts. This parser intentionally
    supports only the 40-byte xWR68xx-style header and makes TLV length
    semantics configurable/auto-detectable instead of silently guessing.
    """

    def __init__(
        self,
        *,
        tlv_length_mode: str = "auto",
        max_packet_bytes: int = 262144,
        max_coordinate_m: float = 50.0,
    ) -> None:
        if tlv_length_mode not in {"auto", "includes_header", "payload_only"}:
            raise ValueError("unsupported TLV length mode")
        self.tlv_length_mode = tlv_length_mode
        self.max_packet_bytes = max_packet_bytes
        self.max_coordinate_m = max_coordinate_m

    @staticmethod
    def _expected_payload_size(tlv_type: int, num_detected: int) -> int | None:
        if tlv_type == TLV_DETECTED_POINTS:
            return num_detected * 16
        if tlv_type == TLV_SIDE_INFO:
            return num_detected * 4
        return None

    def _payload_end(
        self,
        *,
        offset: int,
        tlv_type: int,
        tlv_len: int,
        total_len: int,
        num_detected: int,
    ) -> tuple[int, int, str]:
        payload_start = offset + TLV_HEADER_LEN
        expected = self._expected_payload_size(tlv_type, num_detected)

        if self.tlv_length_mode == "includes_header":
            if tlv_len < TLV_HEADER_LEN:
                raise ValueError("TLV length smaller than TLV header")
            payload_len = tlv_len - TLV_HEADER_LEN
            mode = "includes_header"
        elif self.tlv_length_mode == "payload_only":
            payload_len = tlv_len
            mode = "payload_only"
        else:
            # Known point-cloud TLVs let us disambiguate exactly.
            if expected is not None and tlv_len == expected:
                payload_len = tlv_len
                mode = "payload_only"
            elif expected is not None and tlv_len == expected + TLV_HEADER_LEN:
                payload_len = expected
                mode = "includes_header"
            else:
                # Legacy xWR68xx demos commonly include the TLV header in length;
                # use that as the conservative fallback, while validating bounds.
                if tlv_len >= TLV_HEADER_LEN and offset + tlv_len <= total_len:
                    payload_len = tlv_len - TLV_HEADER_LEN
                    mode = "includes_header"
                elif offset + TLV_HEADER_LEN + tlv_len <= total_len:
                    payload_len = tlv_len
                    mode = "payload_only"
                else:
                    raise ValueError("cannot infer TLV length semantics")

        payload_end = payload_start + payload_len
        if payload_end > total_len:
            raise ValueError("TLV payload exceeds packet boundary")
        return payload_start, payload_end, mode

    def parse_packet(self, packet: bytes, *, timestamp_ns: int | None = None) -> RadarFrame:
        if len(packet) < HEADER_LEN_XWR68XX:
            raise ValueError("packet too short")
        if packet[:8] != MAGIC_WORD:
            raise ValueError("bad magic word")

        (
            version,
            total_len,
            platform,
            frame_number,
            _cpu_cycles,
            num_detected,
            num_tlvs,
            _subframe,
        ) = struct.unpack_from("<8I", packet, 8)

        if total_len < HEADER_LEN_XWR68XX:
            raise ValueError("invalid total packet length")
        if total_len > self.max_packet_bytes:
            raise ValueError("packet exceeds configured safety limit")
        if total_len > len(packet):
            raise ValueError("incomplete packet")
        if num_detected > 10000 or num_tlvs > 256:
            raise ValueError("implausible object/TLV count")

        warnings: list[str] = []
        points: list[RadarPoint] = []
        side_info: list[tuple[float, float]] = []
        offset = HEADER_LEN_XWR68XX

        for tlv_index in range(num_tlvs):
            if offset + TLV_HEADER_LEN > total_len:
                warnings.append(f"TLV {tlv_index}: truncated header")
                break

            tlv_type, tlv_len = struct.unpack_from("<II", packet, offset)
            payload_start, payload_end, mode = self._payload_end(
                offset=offset,
                tlv_type=tlv_type,
                tlv_len=tlv_len,
                total_len=total_len,
                num_detected=num_detected,
            )
            payload = packet[payload_start:payload_end]

            if tlv_type == TLV_DETECTED_POINTS:
                count = min(num_detected, len(payload) // 16)
                for i in range(count):
                    x, y, z, velocity = struct.unpack_from("<4f", payload, i * 16)
                    vals = (x, y, z, velocity)
                    if not all(math.isfinite(v) for v in vals):
                        warnings.append(f"point {i}: non-finite value dropped")
                        continue
                    if max(abs(x), abs(y), abs(z)) > self.max_coordinate_m:
                        warnings.append(f"point {i}: coordinate outside safety bound dropped")
                        continue
                    points.append(RadarPoint(x=x, y=y, z=z, velocity=velocity))

            elif tlv_type == TLV_SIDE_INFO:
                count = min(num_detected, len(payload) // 4)
                for i in range(count):
                    # TI side-info fields are signed int16 in 0.1 dB units.
                    snr_raw, noise_raw = struct.unpack_from("<hh", payload, i * 4)
                    side_info.append((snr_raw * 0.1, noise_raw * 0.1))

            if mode == "includes_header":
                offset = offset + tlv_len
            else:
                offset = payload_end

        for i, (snr, noise) in enumerate(side_info[: len(points)]):
            points[i].snr_db = snr
            points[i].noise_db = noise

        if len(points) != num_detected and num_detected:
            warnings.append(f"header reported {num_detected} points; parsed {len(points)}")

        if version == 0 or platform == 0:
            warnings.append("zero version/platform field")

        return RadarFrame(
            frame_number=frame_number,
            timestamp_ns=timestamp_ns or time.monotonic_ns(),
            points=points,
            parser_warnings=warnings,
        )


class TiIwr6843:
    def __init__(
        self,
        *,
        config_port: str,
        data_port: str,
        profile_path: str,
        config_baud: int = 115200,
        data_baud: int = 921600,
        read_timeout_s: float = 0.2,
        cli_response_timeout_s: float = 0.35,
        tlv_length_mode: str = "auto",
        max_packet_bytes: int = 262144,
        max_coordinate_m: float = 50.0,
    ) -> None:
        self.config_port = config_port
        self.data_port = data_port
        self.profile_path = Path(profile_path)
        self.config_baud = config_baud
        self.data_baud = data_baud
        self.read_timeout_s = read_timeout_s
        self.cli_response_timeout_s = cli_response_timeout_s
        self.max_packet_bytes = max_packet_bytes
        self.cli = None
        self.data = None
        self.parser = TiPacketParser(
            tlv_length_mode=tlv_length_mode,
            max_packet_bytes=max_packet_bytes,
            max_coordinate_m=max_coordinate_m,
        )
        self.buffer = bytearray()
        self.bytes_discarded = 0
        self.malformed_packets = 0

    def connect(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial is required for radar hardware mode")
        if not self.profile_path.exists():
            raise FileNotFoundError(self.profile_path)

        logger.info("Opening TI CLI UART {}", self.config_port)
        self.cli = serial.Serial(
            self.config_port,
            self.config_baud,
            timeout=self.cli_response_timeout_s,
            write_timeout=1,
        )
        logger.info("Opening TI data UART {}", self.data_port)
        self.data = serial.Serial(
            self.data_port,
            self.data_baud,
            timeout=self.read_timeout_s,
        )
        self.cli.reset_input_buffer()
        self.data.reset_input_buffer()
        time.sleep(0.2)
        self._send_profile()

    def _read_cli_response(self) -> str:
        if not self.cli:
            return ""
        deadline = time.monotonic() + self.cli_response_timeout_s
        chunks: list[bytes] = []
        while time.monotonic() < deadline:
            available = self.cli.in_waiting
            if available:
                chunks.append(self.cli.read(available))
                joined = b"".join(chunks).lower()
                if b"done" in joined or b"error" in joined or b"mmwDemo:/>".lower() in joined:
                    break
            else:
                time.sleep(0.01)
        return b"".join(chunks).decode("utf-8", errors="replace")

    def _send_profile(self) -> None:
        if not self.cli:
            raise RuntimeError("CLI UART not open")
        for line_number, raw in enumerate(self.profile_path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("%") or line.startswith("#"):
                continue
            self.cli.write((line + "\n").encode("ascii"))
            self.cli.flush()
            response = self._read_cli_response()
            if "error" in response.lower():
                raise RuntimeError(
                    f"TI CLI rejected profile line {line_number}: {line!r}; response={response!r}"
                )
            if not response:
                logger.debug("No CLI response observed for line {}", line_number)

    def disconnect(self) -> None:
        for port in (self.cli, self.data):
            try:
                if port and port.is_open:
                    port.close()
            except Exception:
                logger.exception("Error while closing TI serial port")
        self.cli = None
        self.data = None

    def read_frame(self) -> RadarFrame | None:
        if not self.data:
            raise RuntimeError("data UART not open")

        chunk = self.data.read(self.data.in_waiting or 4096)
        received_ns = time.monotonic_ns()
        if chunk:
            self.buffer.extend(chunk)

        # Bound memory during corrupt/noisy streams.
        if len(self.buffer) > self.max_packet_bytes * 3:
            keep = max(8, self.max_packet_bytes)
            removed = len(self.buffer) - keep
            del self.buffer[:removed]
            self.bytes_discarded += removed

        start = self.buffer.find(MAGIC_WORD)
        if start < 0:
            if len(self.buffer) > 8192:
                removed = len(self.buffer) - 7
                del self.buffer[:removed]
                self.bytes_discarded += removed
            return None

        if start > 0:
            del self.buffer[:start]
            self.bytes_discarded += start

        if len(self.buffer) < HEADER_LEN_XWR68XX:
            return None

        total_len = struct.unpack_from("<I", self.buffer, 12)[0]
        if total_len < HEADER_LEN_XWR68XX or total_len > self.max_packet_bytes:
            del self.buffer[:8]
            self.bytes_discarded += 8
            return None
        if len(self.buffer) < total_len:
            return None

        packet = bytes(self.buffer[:total_len])
        del self.buffer[:total_len]
        try:
            return self.parser.parse_packet(packet, timestamp_ns=received_ns)
        except Exception as exc:
            self.malformed_packets += 1
            logger.warning("Dropped malformed TI packet: {}", exc)
            return None
