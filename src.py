def stop_points_based_segmentation(trajectories, identifier='mmsi', speed_threshold=1.5, distance_threshold=5, time_threshold=300):
    """
    Given a time sorted ship's trajectory, 'stop_points_calculate' finds the points of the given ship based on 
    the criteria stated by the threshold variables(speed_threshold, distance_threshold).
    
    A candidate stop points is a stop point with speed over ground speed less than the given threshold. For each 
    candidate stop point, the algorithm performs a left search for finding a point Xl given that 
    distance(Xl, candidate_point) <= distance_threshold and a right search. 
    
    If time_difference(Xl, Xr) >= time_threshold then the candidate point is appended at the list of stop points. 
    
    In other words if the ship needed more than the time_threshold to make the distance stated by the distance_threshold
    a stop point exists.
    
    Arguments:
        trajectories {DataFrame} -- Data in Pandas DataFrame format. The geospatial data should be
                                     come along with their mmsi, timestamp and speed.
                                     
        identifier (string) -- Used for aggregating the trajectories dataframe into seperated groups. 
                               By default it's the ship's MMSI. It could also be a custom calculated id.
                                       
        speed_threshold {number} -- The minimum speed that a point must have in order to be 
                                    characterized  a stop point.
                                    
        distance_threshold {number} -- Radius to search around each candidate stop point
        
        time_threshold {number} -- The minimum time to move through the given radius(distance_threshold)
    """
    
    
    temp = []
    traj_id_ = 1
    df = trajectories.copy().sort_values(by=[identifier, 'timestamp'])
    
    for traj_id, sdf in df.groupby(identifier, group_keys=False):
        # Holds the stop points for each MMSI. It gets appended into temp after each iteration
        stop_points = []
        
        # Gets all points with speed lower than the given threshold, i.e candidate stop points
        slow_speed_points = sdf[sdf['speed'] <= speed_threshold].index
            
        k = 0
        while not slow_speed_points.empty and k < len(slow_speed_points):

            i = slow_speed_points[k]
            center = i
            center_k = sdf.loc[i]
            
            # Left Search
            li = side_search(sdf.loc[:center - 1,], center_k, distance_threshold, 3600, i) 
            #Right Search
            ri = side_search(sdf.loc[center + 1:,], center_k, distance_threshold, 3600, i)
            
            # If there is no right or left point closer than the given distance_threshold, moves to
            # the next candidate stop point
                         
            if not li and not ri:
                k = k + 1
                continue
            
            # If a right point exists and not left
            if not li:
                stop_points.append(center)
                try:
                    _next = sdf[sdf['speed'] > speed_threshold].loc[ri + 1:]['timestamp'].idxmin()
                except:
                    break
                slow_speed_points = sdf[sdf['speed'] < speed_threshold].loc[_next:].index
                k = 0
                continue
            
            # If a left point exists and right
            if not ri:
                stop_points.append(center)
                try:
                    _next = sdf[sdf['speed'] > speed_threshold].loc[center + 1:]['timestamp'].idxmin()
                except:
                    break
                slow_speed_points = sdf[sdf['speed'] < speed_threshold].loc[_next:].index
                k = 0
                continue
                
                
            # Time based check
            if (sdf.loc[ri]['timestamp'] - sdf.loc[li]['timestamp']) >= time_threshold:  
                stop_points.append(center)
                try:
                    _next = sdf[sdf['speed'] > speed_threshold].loc[ri + 1:]['timestamp'].idxmin()
                except:
                    break
                    
                slow_speed_points = sdf[sdf['speed'] < speed_threshold].loc[_next:].index
                k = 0
            else:
                k = k + 1
                

        # Mark stop points by creating a new column 
        sdf.loc[stop_points, 'stop'] = 'Yes'
  
        # Group points into trajectories
        last_check = 0
        sdfs = []
        for ind in stop_points[0:]:
            sdfs.append(sdf.loc[last_check:ind])
            last_check = ind + 1
        try:
            sdfs.append(sdf.loc[stop_points[-1]:])
        except:
            pass
        
        for i in range(0,len(sdfs)):  
            sdfs[i].loc[:,'traj_id'] = traj_id_
            traj_id_ = traj_id_ + 1
    

        temp.extend(sdfs) 
    return temp
    
    
def side_search(trajectory, center_point, distance_threshold=5, time_threshold=300):
    copy = trajectory.copy()
    
    copy['d_distance'] = _distance_difference(copy, center_point)
    copy['d_time'] = _time_difference(copy['timestamp'], center_point['timestamp'])
    
    try:
        return co[(co['d_distance'] <= distance_threshold) & (co['d_time'] <= time_threshold)]['d_distance'].idxmax()
    except:
        return None
