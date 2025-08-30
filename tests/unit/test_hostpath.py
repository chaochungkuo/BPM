from bpm.models.hostpath import HostPath

def test_from_raw_local_abs_to_host():
    hp = HostPath.from_raw("/data/run42", current_host="nextgen")
    assert str(hp) == "nextgen:/data/run42"

def test_from_raw_hostaware_kept():
    hp = HostPath.from_raw("web:/var/www", current_host="nextgen")
    assert str(hp) == "web:/var/www"

def test_materialize_with_hosts(hosts_cfg):
    hp = HostPath.from_raw("nextgen:/data/run42", current_host="nextgen")
    assert hp.materialize(hosts_cfg) == "/mnt/nextgen/data/run42"

def test_materialize_missing_host_fallback(hosts_cfg):
    hp = HostPath.from_raw("unknown:/x", current_host="nextgen")
    assert hp.materialize(hosts_cfg, fallback_prefix="/mnt/default") == "/mnt/default/x"

def test_materialize_no_mapping_returns_abs():
    hp = HostPath.from_raw("unknown:/x/y", current_host="nextgen")
    assert hp.materialize({}, fallback_prefix=None) == "/x/y"