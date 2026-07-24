# Normal branching Python module for complexity fixtures.
def compute(a, b, c=0, *args, **kwargs):
    total = 0
    if a > 0 and b > 0:
        for item in args:
            if item:
                total += item
            else:
                while c > 0:
                    c -= 1
                    total += 1
    elif a < 0 or b < 0:
        total = -1
    else:
        total = a + b if c else 0
    try:
        assert total >= -1
    except AssertionError:
        return 0
    return total


class Calculator:
    def __init__(self, seed: int = 0):
        self.seed = seed

    def nested(self, value: int) -> int:
        if value > 0:
            if value > 10:
                for _ in range(value):
                    if self.seed:
                        return value
        return value


def empty_fn():
    pass
