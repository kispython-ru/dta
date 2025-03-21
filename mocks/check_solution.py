TESTS = [{"ИНБО-01-20": [list(range(40)), list(range(40))]}]
GROUPS, TASKS = ["ИНБО-01-20"], [0, 1]


def load_config():
    return GROUPS, TASKS, ''


def check_solution(group, task, variant, code):
    if "42" in code:
        return True, ""
    return False, "An error has occured."
