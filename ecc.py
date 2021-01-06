from random import randint

import hashlib
import hmac


class FieldElement:

    def __init__(self, num, prime):
        if num >= prime or num < 0:
            error = 'Num {} not in field range 0 to {}.'.format(
                    num, prime - 1)
            raise ValueError(error)
        self.num = num
        self.prime = prime

    def __repr__(self):
        return 'FieldElement_{}({})'.format(self.prime,self.num)

    def __eq__(self, other):
        if other is None:
            return False
        return self.prime == other.prime and self.num == other.num

    def __ne__(self, other):
        return not (self == other)

    def __add__(self, other):
        if self.prime != other.prime:
            raise TypeError('Cannot add two numbers in different Fields')
        num = (self.num + other.num) % self.prime
        return self.__class__(num, self.prime)

    def __sub__(self, other):
        if self.prime != other.prime:
            raise TypeError('Cannot subtract two numbers in different Fields')
        num = (self.num - other.num) % self.prime
        return self.__class__(num, self.prime)

    def __mul__(self, other):
        if self.prime != other.prime:
            raise TypeError('Cannot multiply two numbers in different Fields')
        num = (self.num * other.num) % self.prime
        return self.__class__(num, self.prime)

    def __pow__(self, exponent):
        _exponent = exponent % (self.prime - 1)
        num = pow(self.num, _exponent, self.prime)
        return self.__class__(num, self.prime)

    def __truediv__(self, other):
        """ Implementation of Fermat's little theorem
        - self.num**(p-1) % p == 1
        - Thus, 1/n == pow(n, p-2, p)
        """
        if self.prime != other.prime:
            raise TypeError('Cannot divide two numbers in different Fields')
        num = self.num * pow(other.num, self.prime - 2, self.prime) % self.prime
        return self.__class__(num, self.prime)

    # scalar multiplication
    def __rmul__(self, coefficient):
        num = (self.num * coefficient) % self.prime
        return self.__class__(num, self.prime)


class Point:

    def __init__(self, x, y, a, b):
        """Point on elliptic curve"""
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        
        # addition identity, i.e. point of infinity
        if self.x is None and self.y is None:
            return
        if self.y**2 != self.x**3 + a*x + b:
            raise ValueError('({}, {}) is not on the curve'.format(x, y))

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b \
                and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        if self.x is None:
            return 'Point(infinity)'
        elif isinstance(self.x, FieldElement):
            return 'Point({}, {})_{}_{} FieldElement({})'.format(
                    self.x.num, self.y.num, self.a.num, self.b.num, self.x.prime)
        else:
            return 'Point({}, {})_{}_{}'.format(self.x, self.y, self.a, self.b)

    def __add__(self, other):
        if self.a != other.a and self.b != other.b:
            raise TypeError('Points {}, {} are not on the save curve.'.format(self, other))

        # addition with identity
        if self.x is None and self.y is None:
            return other
        if other.y is None and other.y is None:
            return self
        
        if self.x != other.x:
            s = (other.y - self.y) / (other.x - self.x)
            x = s**2 - self.x - other.x
            y = s * (self.x - x) - self.y
            return self.__class__(x, y, self.a, self.b)
        elif self.y != other.y or self.y == 0 * self.x:
            # `0 * self.x`: for the case self.x is FieldElement object
            return self.__class__(None, None, self.a, self.b)
        else:
            s = (3 * self.x**2 + self.a) / (2 * self.y)
            x = s**2 - 2 * self.x
            y = s * (self.x - x) - self.y
            return self.__class__(x, y, self.a, self.b)

    def __rmul__(self, coefficient):
        coef = coefficient
        current = self
        result = self.__class__(None, None, self.a, self.b)
        while coef:
            if coef & 1:
                result += current
            current += current
            coef >>= 1
        return result


# bitcoin-specific elliptic curve - secp256k1
class S256Field(FieldElement):

    def __init__(self, num, prime=None):
        P = 2**256 - 2**32 - 977
        super().__init__(num=num, prime=P)

    def __repr__(self):
        return '{:x}'.format(self.num).zfill(64)


class S256Point(Point):

    def __init__(self, x, y, a=None, b=None):
        a, b = S256Field(0), S256Field(7)
        if type(x) == int:
            super().__init__(x=S256Field(x), y=S256Field(y), a=a, b=b)
        else:
            super().__init__(x=x, y=y, a=a, b=b)

    def __repr__(self):
        if self.x is None:
            return 'S256Point(infinity)'
        else:
            return 'S256Point({}, {})'.format(self.x, self.y)

    def __rmul__(self, coefficient):
        coef = coefficient % N
        return super().__rmul__(coef)

    def verify(self, z, sig):
        s_inv = pow(sig.s, N-2, N)
        u = z * s_inv % N
        v = sig.r * s_inv % N
        R = u * G + v * self
        return R.x.num == sig.r

N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
G = S256Point(
        0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
        0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)


class Signature:

    def __init__(self, r, s):
        self.r = r
        self.s = s

    def __repr__(self):
        return 'Signature({:x},{:x})'.format(self.r, self.s)


class PrivateKey:

    def __init__(self, secret):
        self.secret = secret
        self.point = secret*G

    def hex(self):
        return '{:x}'.format(self.secret).zfill(64)

    def sign(self, z):
        k = self.deterministic_k(z)
        r = (k*G).x.num
        k_inv = pow(k, N-2, N)
        s = (z + r*self.secret) * k_inv % N
        if s > N/2:
            s = N - s
        return Signature(r, s)

    def deterministic_k(self, z):
        k = b'\x00' * 32
        v = b'\x01' * 32
        if z > N:
            z -= N
        z_bytes = z.to_bytes(32, 'big')
        secret_bytes = self.secret.to_bytes(32, 'big')
        s256 = hashlib.sha256
        k = hmac.new(k, v + b'\x00' + secret_bytes + z_bytes, s256).digest()
        v = hmac.new(k, v, s256).digest()
        k = hmac.new(k, v + b'\x01' + secret_bytes + z_bytes, s256).digest()
        v = hmac.new(k, v, s256).digest()
        while True:
            v = hmac.new(k, v, s256).digest()
            candidate = int.from_bytes(v, 'big')
            if candidate >= 1 and candidate < N:
                return candidate
            k = hmac.new(k, v + b'\x00', s256).digest()
            v = hmac.new(k, v, s256).digest()
