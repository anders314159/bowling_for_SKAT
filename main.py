# This script calculates the running sum of a game of traditional 10 pin bowling
# It does not work "online", as in, getting the results of the rolls one by one.
# Instead, it relied on the fact that the REST API sends the entire game at once.
import requests
import numpy as np
from typing import List


# Helper functions
def is_strike(bowling_frame: List[int]):
    return bowling_frame[0] == 10


def is_spare(bowling_frame: List[int]):
    return (bowling_frame[0] + bowling_frame[1] == 10) and not is_strike(bowling_frame)


# The max number of "frames" we can receive is 11 because the API considers the possible 3 roll
# 10th frame as two frames.
max_len_game = 11


def calculate_score(points: List[List[int]]):
    # The arrays are pre-allocated, which is not need for a project of this size,
    # but nevertheless a good idea in-case the rules expand to a large number of frames
    spares, strikes = np.zeros(max_len_game, dtype=bool), np.zeros(max_len_game, dtype=bool)
    points_in_frame, scores = np.zeros(max_len_game, dtype=int), np.zeros(max_len_game, dtype=int)

    # The main idea is to first iterate over the points to calculate out a "base" score for each frame,
    # and then do a second pass to add any bonuses.

    # First pass. The spares, strikes, and points for each frame is calculated.
    i_frame = 0
    for frame in points:
        spares[i_frame] = is_spare(frame)
        strikes[i_frame] = is_strike(frame)
        points_in_frame[i_frame] = frame[0] + frame[1]
        i_frame += 1

    # Second pass. Calculate bonuses. The only real corner case is the 11th frame existing.
    i_frame = 0
    for frame in points:
        # The base amount of points for the frame
        scores[i_frame] = points_in_frame[i_frame]

        # If there is an "extra" 11th frame
        if len(points) == max_len_game:
            # If we are currently looking at the 10th frame
            if i_frame == max_len_game - 2:
                # Just add the points from the 11th frame to the 10th frame
                scores[i_frame] += points_in_frame[max_len_game - 1]
                break
        # If we are the at the last frame BUT it is not the coveted 11th frame, no bonus rolls are added
        if i_frame == len(points) - 1:
            break

        # If the current frame is a strike, we need to add the next two ROLLS
        if strikes[i_frame]:
            # And if the next frame is also strike, we need to "skip" a roll from the next frame
            if strikes[i_frame + 1]:
                scores[i_frame] += points[i_frame + 1][0] + points[i_frame + 2][0]
            # If the next frame is NOT a strike, we just use the two bonuses
            else:
                scores[i_frame] += points[i_frame + 1][0] + points[i_frame + 1][1]

        # If this frame is a spare, we add the next roll
        if spares[i_frame]:
            scores[i_frame] += points[i_frame + 1][0]
        i_frame += 1

    # Remove any trailing zeros
    res_len = min(len(points), max_len_game - 1)
    res = np.cumsum(scores[:res_len]).tolist()
    return res


# """Tests"""
# The amount of air quotes is to indicate that this is not a sufficient test suite.
# We just ask the API for a bunch of games and hope that covers it.
website = "http://13.74.31.101/api/points"
n_tests = 40
# An array of False
tests = np.zeros(n_tests, dtype=bool)
for i in range(n_tests):
    # Ask the API for a game
    bowling_history = requests.get(website)
    points = bowling_history.json()["points"]
    token = bowling_history.json()["token"]

    # Send the calculated sum back
    response = requests.post(website, json={"token": token, "points": calculate_score(points)})

    # Store the result of the response
    tests[i] = response.json()["success"]

# If all the tests passed, indicate that
if np.all(tests):
    print("All the tests passed.")
