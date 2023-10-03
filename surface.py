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
    u = stl_triangles[:,0:2]                        # Create an Array with the normalvector values
    v = np.zeros_like(u)                            # Create the same shaped Vector
    v[:,:1] = u[:,:1]                               # Copy everything but the z-values
    c = np.dot(u,v) / (np.norm(u) * np.norm(v))     # -> cosine of the angle
    calc_angle = np.arccos(np.clip(c, -1, 1))       # Calculate the angle between the 2 vectors
    #filtered_array = np.delete(np.take(stl_triangles, [3,4,5,6,7,8,9,10,11], axis= 1), np.where(calc_angle > max_angle)) # deletes all Indexes in the main Array where the angles > max_angle
    filtered_array = np.delete(stl_triangles[:,3:], np.where(calc_angle > max_angle)[0], axis=0) # deletes all Indexes in the main Array where the angles > max_angle
    surface_points = np.concatenate((np.take(filtered_array, [0,1,2], axis= 1), np.take(filtered_array, [3,4,5], axis= 1), np.take(filtered_array, [6,7,8], axis= 1)), axis=0) # convert all points into 1 array
    surface_filtered = np.unique(surface_points, axis=0) # Delete every duplicate point in the array
    
    ##  surface_filtered contains x,y,z points of the surface
    #   surface_filtered[x, y, z]
    
    return surface_filtered



## Input:  points       -> give the wanted interpolated Points in an [n,2] numpy Array
#          func_points  -> the given datapoints of the Surface

## Use:    Interpolation of the given Points of the Surface with finite Points

## Output: 3 Numpy Array with the Shape [n,n]

def interpolate_grid(points, func_points):
       
    [xmesh, ymesh] = np.meshgrid(points[:,0], points[:,1])
    
    # Create the interpolated grid  -> method = {‘linear’, ‘nearest’, ‘cubic’}
    zmesh = griddata([func_points[:,0],func_points[:,1]], func_points[:,2], (xmesh, ymesh), method='linear')
      
    return xmesh, ymesh, zmesh.T


## Input:  Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] 

## Use:    Calculates the 2d outline from an object

## Output:  Points of the Outline only -> points inside are not included
#           Numpy Array of shape [n,2] where x_points = [:,0] and y_points = [:,1]

def outline_detect(stl_triangles):
    # delete all Triangles, where z1 or z2 or z3 isn't zero
    base_height = np.delete(stl_triangles[:,3:],np.where(stl_triangles[:,2:9:3] > 0)[0],axis=0) 
    base_points_triangles = np.concatenate((np.take(base_height, [0,1,2], axis= 1), np.take(base_height, [3,4,5], axis= 1), np.take(base_height, [6,7,8], axis= 1)), axis=0) # convert all points into 1 array
    base_points = np.unique(base_points_triangles, axis=0) # Delete every duplicate point in the array
    
    return base_points