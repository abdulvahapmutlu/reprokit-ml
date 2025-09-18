from reprokit.determinism import enable


def test_numpy_seed_repeatable():
    import pytest

    np = pytest.importorskip("numpy")

    enable(42, torch=False, tf=False, jax=False)
    a = np.random.rand(5)

    enable(42, torch=False, tf=False, jax=False)
    b = np.random.rand(5)

    assert (a == b).all()
