import pandas as pd
import numpy as np

from utils import calculations
from utils import constants


def filter_by_speed(trajectory, uid=constants.SHIP_ID, speed_limit=constants.SPEED_LIMIT, keep_new_columns=False):
    if keep_new_columns:
        traj = trajectory.copy(deep=True)
    else:
        traj = trajectory.copy(deep=False)

    traj['tmp_time_difference'] = traj.groupby(uid).apply(calculations.calculate_time_difference())
    traj['tmp_dist_difference'] = traj.groupby(uid).apply(calculations.calculate_distance())
    traj['temp_real_speed'] = traj.groupby(uid).apply(calculations.calculate_speed())

    return traj[traj['temp_real_speed'] <= speed_limit]
