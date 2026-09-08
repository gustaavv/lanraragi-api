def test_fixture(sample_user):
    assert sample_user is not None
    assert sample_user["username"] == "dev_user"
