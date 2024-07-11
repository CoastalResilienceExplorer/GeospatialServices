from utils.redis import r
import os
from flask import request
import shutil

def get_paths(project, key):
    paths_to_create = ["init", "flooding", "damages", "exposure", "population", "downloads", "damages_scaled"]
    base = os.path.join(os.getenv("MOUNT_PATH"), project, key)
    paths = {i: os.path.join(base, i) for i in paths_to_create}
    paths['BASE'] = base
    return paths


def save_submission(data, submission_id):
    SUBMISSION_DIR = f"{os.getenv('MOUNT_PATH')}/submissions"
    if os.path.exists(os.path.join(SUBMISSION_DIR, submission_id)):
        os.remove(os.path.join(SUBMISSION_DIR, submission_id))
    with open(os.path.join(SUBMISSION_DIR, submission_id), 'wb') as f:
        f.write(data)


def initialize_paths(paths):
    for v in paths.values():
        if not os.path.exists(v):
            os.makedirs(v)

def setup(SUBMISSION_ID, PROJECT, KEY, TASKS, CLEAN_SLATE=True):

    paths = get_paths(PROJECT, KEY)

    r.delete(SUBMISSION_ID)

    r.hset(SUBMISSION_ID, mapping={
        "status": "STARTED",
        "tasks": ','.join(TASKS),
        "project": PROJECT,
        "key": KEY
    })

    if CLEAN_SLATE:
        if os.path.exists(paths['BASE']):
            shutil.rmtree(paths['BASE'])

    initialize_paths(paths)
    return paths