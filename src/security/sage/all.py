from __future__ import annotations

import functools
import math
import operator
from builtins import round as _python_round

import mpmath
import scipy.optimize
import scipy.special
import scipy.stats

oo = math.inf
pi = math.pi
e = math.e
euler_gamma = float(mpmath.euler)


class Real(float):
    def __new__(cls, value=0.0, prec: int = 53):
        obj = float.__new__(cls, value)
        obj._prec = prec
        return obj

    def _coerce(self, value):
        return Real(value, self._prec)

    def __add__(self, other):
        return self._coerce(float(self) + float(other))

    def __radd__(self, other):
        return self._coerce(float(other) + float(self))

    def __sub__(self, other):
        return self._coerce(float(self) - float(other))

    def __rsub__(self, other):
        return self._coerce(float(other) - float(self))

    def __mul__(self, other):
        return self._coerce(float(self) * float(other))

    def __rmul__(self, other):
        return self._coerce(float(other) * float(self))

    def __truediv__(self, other):
        return self._coerce(float(self) / float(other))

    def __rtruediv__(self, other):
        return self._coerce(float(other) / float(self))

    def __floordiv__(self, other):
        return math.floor(float(self) / float(other))

    def __rfloordiv__(self, other):
        return math.floor(float(other) / float(self))

    def __pow__(self, other):
        try:
            return self._coerce(float(self) ** float(other))
        except OverflowError:
            return self._coerce(oo)

    def __rpow__(self, other):
        try:
            return self._coerce(float(other) ** float(self))
        except OverflowError:
            return self._coerce(oo)

    def __neg__(self):
        return self._coerce(-float(self))

    def __abs__(self):
        return self._coerce(abs(float(self)))

    def sqrt(self):
        return self._coerce(math.sqrt(float(self)))

    def n(self, _digits=None):
        return self

    def prec(self):
        return self._prec

    def round(self, mode=None):
        if mode == "down":
            return math.floor(float(self))
        if mode == "up":
            return math.ceil(float(self))
        return _python_round(float(self))

    def is_NaN(self):
        return math.isnan(float(self))


class RealRing:
    def __init__(self, prec: int = 53):
        self._prec = prec

    def __call__(self, value=0.0):
        return Real(value, self._prec)

    def prec(self):
        return self._prec

    def pi(self):
        return Real(pi, self._prec)


class RationalRing(RealRing):
    pass


class IntegerRing:
    def __call__(self, value=0):
        if value in (oo, -oo):
            return value
        return int(value)


RR = RealRing(53)
RDF = RealRing(53)
QQ = RationalRing(53)
ZZ = IntegerRing()


def RealField(prec: int = 53):
    return RealRing(prec)


def parent(value):
    if isinstance(value, Real):
        return RealRing(value.prec())
    return RealRing(53)


def _wrap(value):
    if isinstance(value, int):
        return value
    return Real(value)


def ceil(value):
    return math.ceil(float(value))


def floor(value):
    return math.floor(float(value))


def round(value, ndigits=None):
    if isinstance(ndigits, str):
        return Real(value).round(ndigits)
    if ndigits is None:
        return _python_round(float(value))
    return _python_round(float(value), ndigits)


def sqrt(value):
    return Real(math.sqrt(float(value)))


def exp(value):
    try:
        return Real(math.exp(float(value)))
    except OverflowError:
        return Real(oo)


def log(value, base=None):
    value = float(value)
    if base is None:
        return Real(math.log(value))
    return Real(math.log(value, float(base)))


def erf(value):
    return Real(math.erf(float(value)))


def tanh(value):
    return Real(math.tanh(float(value)))


def coth(value):
    return Real(1.0 / math.tanh(float(value)))


def zeta(value):
    return Real(mpmath.zeta(float(value)))


def binomial(n, k):
    n = int(n)
    k = int(k)
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def prod(values, start=1):
    return functools.reduce(operator.mul, values, start)


def cached_function(func=None, **_kwargs):
    if func is None:
        return lambda wrapped: functools.lru_cache(maxsize=None)(wrapped)
    return functools.lru_cache(maxsize=None)(func)


def find_root(func, a, b, **kwargs):
    xtol = kwargs.get("xtol", kwargs.get("rtol", 1e-12))
    return Real(scipy.optimize.brentq(lambda x: float(func(x)), float(a), float(b), xtol=xtol))


class RealDistribution:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def cum_distribution_function(self, x):
        if self.name == "chisquared":
            return Real(scipy.stats.chi2.cdf(float(x), float(self.params)))
        if self.name == "beta":
            a, b = self.params
            return Real(scipy.stats.beta.cdf(float(x), float(a), float(b)))
        raise NotImplementedError(f"RealDistribution({self.name!r})")


def line(*_args, **_kwargs):
    return None


def var(*_args, **_kwargs):
    return None


def find_fit(*_args, **_kwargs):
    raise NotImplementedError("find_fit is only used in documentation examples")


class PowerSeriesRing:
    def __init__(self, *_args, **_kwargs):
        pass

    def __call__(self, *_args, **_kwargs):
        raise NotImplementedError("PowerSeriesRing is not needed for SetA/UniX security validation")

    def gen(self):
        raise NotImplementedError("PowerSeriesRing is not needed for SetA/UniX security validation")
