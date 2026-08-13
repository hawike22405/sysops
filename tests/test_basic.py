import json
from src.sysops import probes

def test_collect_all_keys():
    data = probes.collect_all()
    assert isinstance(data, dict)
    assert "os" in data
    assert "host" in data
    assert "cpu" in data
    assert "memory" in data
