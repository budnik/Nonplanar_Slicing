# This file creates a Mesh for the top Surface of the stl File
from scipy.interpolate import griddata
import numpy as np

## Input:   Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
           #maximum of the possible angle for the surface 

## Use:     Calculates the angle between every normalvector and the horizontal plane

## Output:  gives back 3 Columnvectors: 2 coordinates with the corresponding z value

def create_surface(stl__triangles, max_angle):
    stl_triangles = np.zeros([10, 12],dtype=float)
    #to be programmed ----------------------
    u = stl_triangles[:,:,:]             # Create an Array with the normalvector values
    v = np.zeros_like(u)                        # Create the same shaped Vector
    v[:,:,] = u[:,:,]                           # Copy everything but the z-values
    c = np.dot(u,v) / (np.norm(u) * np.norm(v)) # -> cosine of the angle
    calc_angle = np.arccos(np.clip(c, -1, 1))        # Calculate the angle between the 2 vectors
    #np.take(stl_triangles, [3,4,5,6,7,8,9,10,11], axis= None)
    filtered_array = np.delete(np.take(stl_triangles, [3,4,5,6,7,8,9,10,11], axis= 1), np.where(calc_angle > max_angle)) # deletes all Indexes in the main Array where the angles > max_angle
    surface_points = np.concatenate((np.take(filtered_array, [0,1,2], axis= 1), np.take(filtered_array, [3,4,5], axis= 1), np.take(filtered_array, [6,7,8], axis= 1)), axis=0) # convert all points into 1 array
    surface_filtered = np.unique(surface_points, axis=0) # Delete every duplicate point in the array
    
    ##  surface_filtered contains x,y,z points of the surface
    #   surface_filtered[x, y, z]
    
    ## Create the Grid and interpolate within
    
    x_min = min(surface_filtered[:,0])
    x_max = max(surface_filtered[:,0])
    y_min = min(surface_filtered[:,1])
    y_max = max(surface_filtered[:,1])
    
    resolution = 20
    
    # Create a Meshgrid
    [xmesh, ymesh] = np.meshgrid(np.linspace(np.round(x_min,1),np.round(x_max,1), resolution), np.linspace(np.round(y_min,1), np.round(y_max,1), resolution))
    # Create the interpolated grid  -> method = {‘linear’, ‘nearest’, ‘cubic’}
    
    grid_interpolated = griddata([surface_filtered[:,0],surface_filtered[:,1]], surface_filtered[:,2], (xmesh, ymesh), method='linear')
        
    return grid_interpolated