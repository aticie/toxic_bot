class Point(tuple):
    def __new__(cls, x, y):
        return tuple.__new__(Point, (x, y))

    def __add__(self, other):
        return Point(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return Point(self[0] - other[0], self[1] - other[1])

    def __truediv__(self, other):
        return Point(self[0] / other, self[1] / other)

    def __floordiv__(self, other):
        return Point(self[0] // other, self[1] // other)

    @classmethod
    def from_tuple(cls, t):
        return cls(t[0], t[1])


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton
