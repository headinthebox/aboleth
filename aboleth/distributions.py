"""Model parameter distributions."""
import numpy as np
import tensorflow as tf

from aboleth.util import pos


#
# Generic prior and posterior classes
#

class Normal:
    """
    Normal (IID) prior/posterior.

    Parameters:
        mu : Tensor
            mean, shape [d_i, d_o]
        var : Tensor
            variance, shape [d_i, d_o]
    """

    def __init__(self, mu=0., var=1.):
        self.mu = mu
        self.var = var
        self.sigma = tf.sqrt(var)
        self.D = tf.shape(mu)

    def sample(self):
        # Reparameterisation trick
        e = tf.random_normal(self.D)
        x = self.mu + e * self.sigma
        return x

    def KL(self, p):
        KL = 0.5 * (tf.log(p.var) - tf.log(self.var) + self.var / p.var - 1. +
                    (self.mu - p.mu)**2 / p.var)
        return KL


class Gaussian:
    """
    Gaussian prior/posterior.

    Parameters:
        mu : Tensor
            mean, shape [d_i, d_o]
        L : Tensor
            Cholesky, shape [d_o, d_i, d_i]
    """

    def __init__(self, mu, L):
        self.mu = tf.expand_dims(tf.transpose(mu), 2)  # O x I x 1
        self.L = L  # O x I x I
        self.d = tf.shape(mu)
        self.D = tf.shape(self.mu)

    def sample(self):
        e = tf.random_normal(self.D)
        x = tf.reshape(self.mu + tf.matmul(self.L, e), self.d)
        return x

    def KL(self, p):
        """KL between self and univariate prior, p."""
        D = tf.to_float(self.D)
        tr = tf.reduce_sum(self.L * self.L) / p.var
        dist = tf.nn.l2_loss(p.mu - tf.reshape(self.mu, self.d)) / p.var
        logdet = D * tf.log(p.var) - _chollogdet(self.L)
        KL = 0.5 * (tr + dist + logdet - D)
        return KL


#
# Streamlined interfaces for initialising the priors and posteriors
#

def norm_prior(dim, var, learn_var):
    mu = np.zeros(dim, dtype=np.float32)
    var = pos(tf.Variable(var)) if learn_var else var
    P = Normal(mu, var)
    return P


def norm_posterior(dim, var0):
    mu = np.sqrt(var0) * np.random.randn(*dim)
    mu = tf.Variable((mu.astype(np.float32)))
    var = var0 * np.random.randn(*dim)
    var = pos(tf.Variable(var.astype(np.float32)))
    Q = Normal(mu, var)
    return Q


def gaus_posterior(dim, var0):
    I, O = dim
    sig0 = np.sqrt(var0)
    mu = (np.random.randn(I, O) * sig0).astype(np.float32)
    Le = np.tile(np.eye(I, dtype=np.float32), [O, 1, 1]) * np.sqrt(var0)
    L = tf.matrix_band_part(tf.Variable(Le), -1, 0)

    # l = (sig0 * np.random.randn(I * (I - 1) // 2, O)).astype(np.float32)
    # l = tf.Variable(l)
    # u, v = np.tril_indices(I, -1)
    # indices = (u * I + v)[:, np.newaxis]
    # L = tf.scatter_nd(indices, l, shape=(I * I, O))
    # L = tf.reshape(L, (O, I, I))

    Q = Gaussian(mu, L)
    return Q


#
# Private module stuff
#

def _chollogdet(L):
    """L is [..., D, D]."""
    l = tf.matrix_diag_part(L)
    logdet = 2. * tf.reduce_sum(tf.log(l))
    return logdet