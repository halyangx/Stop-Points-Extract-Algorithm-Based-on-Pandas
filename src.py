import pandas as pd

def side_search(partitioned_trajectory, center_point, distance_threshold, time_threshold, speed_threshold):
    """
    Used for calculating the left and right limits of a trajectory given a center point and the needed conditions.
    """
    
    copy = partitioned_trajectory.copy(deep=False)
    # Calculates the haversine distance between the center and the remaining side points
    copy['d_distance'] = _distance_difference(copy, center_point)
    # Calculates the time difference between the center and the ramining side points
    copy['d_time'] = np.abs(copy['timestamp'] - center_point['timestamp'])

    try:
        # If a point that satisfying the above conditions exists, return it
        # otherwise reutrn None
        return copy[
            (copy['d_distance'] <= distance_threshold) 
            & (copy['d_time'] <= 3600)]['d_distance'].idxmax()
    except ValueError:
        return None


    
def stop_points_based_segmentation(trajectories, identifier='second_pass', speed_threshold=2.0, distance_threshold=5.0, time_threshold=300):
    """
    Given a DataFrame with lon, lat, timestamp, speed and an identifier column where each row describes a time ordered
    gps point, 'stop_points_based_segmentation' calculates the stop points and segments the DataFrame into individual
    trips with a beginning and end.
    
    Step 1:
    For each unique identifier(could be a ship's MMSI or generally a number that describes unique moving objects) the
    algorithms begins by calculating the candidate stop points. A candidate stop point is simply a point with moving speed
    less than the given parameter for the speed_threshold.
    
    Step 2:
    For each candidate stop point, the algorithm performs a left search with radius given by the distance_threshold. For
    example if the given threshold is 2 nautical miles it searches for all points under the distance bound that has a speed
    higher than the threshold and time difference lower than the time_threshold. From these points it returns the one with the
    higher distance. The same procedure goes by for the right part of the trajectory.
    
    Step 3:
    If the time difference between the left and the right limit is more than the given time threshold then the point is assigned
    to the stop points set and the algorithm continious inspecting the other candidates points. In other words if the moving
    object completed the distance between the left and the right point in more than the threshold the center this distance
    is a stop point.
    
    ***
    For the 2nd step we could just loop through the left and right of each point and stop when the distance's limit is
    exceeded. We choosed not to follow this approach as Python's higher level loops where not as efficienty as Pandas
    indexing and selecting. 
    
    Thus during selecting the row with maximum distance under the given distance threshold we introduce one more conditional 
    check, the time based one. By this way, we avoid choosing left/right limits that are close in distance but have 
    a high time difference. Imagine if the moving object passed by the same spot before without stoping, it would be under 
    the distance threshould but this could have happened at different time - window.
    
    
    Arguments:
        trajectories {DataFrame} -- Data in Pandas DataFrame format. The geospatial data should be
                                     come along with their identifier, speed, lon, lat and timestamp
                                     columns.
                                     
        identifier (int) -- Used for aggregating the trajectories dataframe into seperated groups. 
                            By default it's the ship's MMSI. It could also be a custom calculated id.
                                       
        speed_threshold {number} -- The minimum speed that a point must have in order to be 
                                    characterized  a stop point.
                                    
        distance_threshold {number} -- Radius to search around each candidate stop point
        
        time_threshold {number} -- The minimum time to move through the given radius(distance_threshold)
    """
    
    temp = []
    traj_id_ = 1

    for traj_id, sdf in trajectories.groupby(identifier, group_keys=False):
        grp_copy = sdf.copy(deep=False).reset_index(drop=True).sort_values(by='timestamp', ascending=True)
        
        # Stop points for each group
        stop_points = []    
        # Candidates points
        slow_speed_points = grp_copy[grp_copy['calc_speed'] <= speed_threshold].index
        
        candidates_index = 0
        while not slow_speed_points.empty and candidates_index < len(slow_speed_points):
            center = slow_speed_points[candidates_index]
            center_row = grp_copy.iloc[center]
            
            # Left Search
            li = side_search(grp_copy.iloc[:center], center_row, distance_threshold, time_threshold, speed_threshold)
            # Right Search
            ri = side_search(grp_copy.iloc[center + 1:], center_row, distance_threshold, time_threshold, speed_threshold)
                 
            # If there is no right or left point closer than the given distance_threshold, moves to
            # the next candidate stop point
            
            if li is None or ri is None:
                candidates_index = candidates_index + 1
                continue
                

        
            left_limit = grp_copy.iloc[li]
            right_limit = grp_copy.iloc[ri]

            
            if (right_limit['timestamp'] - left_limit['timestamp']) >= time_threshold:  
                stop_points.append(center)
                
                try:
                    # If we are not at the end of the dataframe
                    _next = grp_copy.iloc[ri + 1:][grp_copy['calc_speed'] > speed_threshold]['timestamp'].idxmin()
                    slow_speed_points = grp_copy.iloc[_next:][grp_copy['calc_speed'] <= speed_threshold].index
                    candidates_index = 0
                    
                except ValueError:
                    break
            else:
                candidates_index = candidates_index + 1
                
            
        
        
        # Mark stop points
        grp_copy.loc[stop_points, 'stop'] = 'Yes'
  
        # Segment trips based on stop - points index position
        last_check = 0
        sdfs = []
        for ind in stop_points:
            sdfs.append(grp_copy.iloc[last_check:ind + 1])
            last_check = ind + 1
        
        for i in range(0,len(sdfs)):  
            sdfs[i].loc[:,'traj_id'] = traj_id_
            traj_id_ = traj_id_ + 1
    
    
        temp.extend(sdfs) 
    
    return pd.concat(temp)
