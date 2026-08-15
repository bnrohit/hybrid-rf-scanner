import struct

from hybrid_scanner.radar.ti_iwr6843 import MAGIC_WORD, TiPacketParser


def build_packet(*, mode: str, snr_raw: int = 123):
    points_payload = struct.pack("<4f", 1.0, 2.0, 3.0, 0.5)
    side_payload = struct.pack("<hh", snr_raw, -40)

    def tlv(t, payload):
        length = len(payload) + 8 if mode == "includes_header" else len(payload)
        return struct.pack("<II", t, length) + payload

    body = tlv(1, points_payload) + tlv(7, side_payload)
    total_len = 40 + len(body)
    header = MAGIC_WORD + struct.pack("<8I", 0x03060002, total_len, 0xA6843, 42, 100, 1, 2, 0)
    return header + body


def test_parse_includes_header():
    frame = TiPacketParser(tlv_length_mode="auto").parse_packet(build_packet(mode="includes_header"))
    assert frame.frame_number == 42
    assert len(frame.points) == 1
    assert frame.points[0].snr_db == 12.3
    assert frame.points[0].noise_db == -4.0


def test_parse_payload_only():
    frame = TiPacketParser(tlv_length_mode="auto").parse_packet(build_packet(mode="payload_only"))
    assert len(frame.points) == 1
    assert frame.points[0].x == 1.0


def test_signed_side_info():
    frame = TiPacketParser(tlv_length_mode="auto").parse_packet(
        build_packet(mode="includes_header", snr_raw=-15)
    )
    assert frame.points[0].snr_db == -1.5
