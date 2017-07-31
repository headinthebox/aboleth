"""Test the ops module."""
import numpy as np
import tensorflow as tf
import aboleth as ab


def test_stack2():
    """Test base implementation of stack."""
    def f(X):
        return "f({})".format(X), 10.0

    def g(X):
        return "g({})".format(X), 20.0

    h = ab.ops._stack2(f, g)

    tc = tf.test.TestCase()
    with tc.test_session():
        phi, loss = h(X="x")
        assert phi == "g(f(x))"
        assert loss.eval() == 30.0


def test_stack2_multi():
    """Test base implementation of stack."""
    def f(X, Y):
        return "f({}, {})".format(X, Y), 10.0

    def g(X):
        return "g({})".format(X), 20.0

    h = ab.ops._stack2(f, g)

    tc = tf.test.TestCase()
    with tc.test_session():
        phi, loss = h(X="x", Y="y")
        assert phi == "g(f(x, y))"
        assert loss.eval() == 30.0


def test_stack(mocker):
    """Test stack another way with mocking."""
    mocked_reduce = mocker.patch('aboleth.ops.reduce')
    f = mocker.MagicMock()
    g = mocker.MagicMock()
    h = mocker.MagicMock()
    ab.stack(f, g, h)
    mocked_reduce.assert_called_once_with(ab.ops._stack2, (f, g, h))


def test_stack_real():
    """Test implementation of stack."""
    def f(X, Y):
        return "f({}, {})".format(X, Y), 10.0

    def g(X):
        return "g({})".format(X), 20.0

    def h(X):
        return "h({})".format(X), 5.0

    h = ab.stack(f, g, h)

    tc = tf.test.TestCase()
    with tc.test_session():
        phi, loss = h(X="x", Y="y")
        assert phi == "h(g(f(x, y)))"
        assert loss.eval() == 35.0


def test_concat(make_data):
    """Test concatenation op."""
    x, _, X = make_data

    # This replicates the input layer behaviour
    def f(**kwargs):
        return kwargs['X'], 0.0

    def g(**kwargs):
        return kwargs['Y'], 0.0

    catlayer = ab.concat(f, g)

    F, KL = catlayer(X=X, Y=X)

    tc = tf.test.TestCase()
    with tc.test_session():
        forked = F.eval()
        orig = X.eval()
        assert forked.shape == orig.shape[0:2] + (2 * orig.shape[2],)
        assert np.all(forked == np.dstack((orig, orig)))
        assert KL.eval() == 0.0


def test_slicecat(make_data):
    """Test concatenation  of slices op."""
    x, _, X = make_data

    def make_idxlayer(i):
        def idlayer(X):
            return X + i, float(i)
        return idlayer

    catlayer = ab.slicecat(make_idxlayer(2), make_idxlayer(3))
    F, KL = catlayer(X)

    tc = tf.test.TestCase()
    with tc.test_session():
        catted = F.eval()
        orig = X.eval()
        assert catted.shape == orig.shape
        assert np.allclose(catted[:, :, 0], orig[:, :, 0] + 2)
        assert np.allclose(catted[:, :, 1], orig[:, :, 1] + 3)
        assert KL.eval() == 5.0


def test_add(make_data):
    """Test the add join."""
    x, _, X = make_data

    # This replicates the input layer behaviour
    def f(**kwargs):
        return kwargs['X'], 0.0

    def g(**kwargs):
        return kwargs['Y'], 0.0

    addlayer = ab.add(f, g)

    F, KL = addlayer(X=X, Y=X)

    tc = tf.test.TestCase()
    with tc.test_session():
        forked = F.eval()
        orig = X.eval()
        assert forked.shape == orig.shape
        assert np.all(forked == 2 * orig)
        assert KL.eval() == 0.0
