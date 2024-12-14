import hashlib
import json

def hash_problem(problem: dict):
    problem_dict = {
        "problem": problem["problem"],
        "options": problem["options"],
    }

    problem_json = json.dumps(problem_dict, sort_keys=True).encode('utf-8')
    return hashlib.sha256(problem_json).hexdigest()