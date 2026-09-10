def test_get_server_information(api):
    si = api.misc.get_server_information()
    assert si.version == "0.9.81"
    assert si.nofun_mode
