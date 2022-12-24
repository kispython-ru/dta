import random


def analyze_solution(task, code):
    rnd = random.randint(0, 2)
    if rnd == 0:
        return True, 0
    if rnd == 1:
        return True, 1
    return False, 2
