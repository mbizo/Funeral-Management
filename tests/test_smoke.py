def test_import():
    import run
    assert hasattr(run, "app")
