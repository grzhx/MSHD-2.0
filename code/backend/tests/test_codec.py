import pytest
from codec import codec
from codec.codec import ID_TOTAL_LENGTH

EXAMPLE_ID = "632626200206202105220204001010302001"


def test_decode_example_id():
    record = codec.decode_disaster(EXAMPLE_ID)
    assert record.id == EXAMPLE_ID
    assert record.event.location_code == "632626200206"
    assert record.event.time_code == "20210522020400"
    assert record.source.code == "101"
    assert record.carrier.code == "0"
    assert record.disaster.category == "3"
    assert record.disaster.sub_category == "02"
    assert record.disaster.indicator == "001"


def test_encode_decode_roundtrip():
    event = codec.build_event_info("632626200206", "2021-05-22T02:04:00Z")
    source = codec.build_source_info("101")
    carrier = codec.build_carrier_info("0")
    disaster = codec.build_disaster_info("3", "02", "001")
    encoded = codec.encode_disaster(event, source, carrier, disaster)
    assert len(encoded) == ID_TOTAL_LENGTH
    decoded = codec.decode_disaster(encoded)
    assert decoded.id == encoded
    assert decoded.names["indicator"]


def test_invalid_length():
    with pytest.raises(ValueError):
        codec.decode_disaster("123")
