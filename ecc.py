
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
        return FieldElement(num, self.prime)

    def __sub__(self, other):
        if self.prime != other.prime:
            raise TypeError('Cannot subtract two numbers in different Fields')
        num = (self.num - other.num) % self.prime
        return FieldElement(num, self.prime)

    def __mul__(self, other):
        if self.prime != other.prime:
            raise TypeError('Cannot multiply two numbers in different Fields')
        num = (self.num * other.num) % self.prime
        return FieldElement(num, self.prime)

    def __pow__(self, exponent):
        _exponent = exponent % (self.prime - 1)
        num = pow(self.num, _exponent, self.prime)
        return FieldElement(num, self.prime)

    def __truediv__(self, other):
        """ Implementation of Fermat's little theorem
        - self.num**(p-1) % p == 1
        - Thus, 1/n == pow(n, p-2, p)
        """
        if self.prime != other.prime:
            raise TypeError('Cannot divide two numbers in different Fields')
        num = self.num * pow(other.num, self.prime - 2, self.prime) % self.prime
        return FieldElement(num, self.prime)


class Point:

    def __init__(self, x, y, a, b):
        """Point on elliptic curve"""
        self.a = a
        self.b = b
        self.x = x
        self.y = y
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
        else:
            return 'Poinrt({}, {})_{}_{}'.format(self.x, self.y, self.a, self.b)

