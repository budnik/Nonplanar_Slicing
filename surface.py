# This file creates a Mesh for the top Surface of the stl File
from scipy.interpolate import griddata
import numpy as np

## Input:   gets the openend STL file for further manipulation

## Use:     gets the top surface of the stl object

## Output:  gives back 3 Columnvectors: 2 coordinates with the corresponding z value

def create_surface(stl_file_object):
    #to be programmed ----------------------
    
    
    
    r = np.zeros((20,3))
    return r[:,0], r[:,1], r[:,2]
    
    

## Input:   gets the x, y, z Values of the Surface as 3 columnvectors
##          param: N equals the number of evenly spaced points
## Output: 
def interpolate_surface(x,y,z,resolution = 100):
    #calculate the min / max Values from the vectors
    x_min = min(x)
    x_max = max(x)
    y_min = min(y)
    y_max = max(y)
    z_min = min(z)
    z_max = max(z)
    #Create a Meshgrid
    [xmesh, ymesh] = np.meshgrid(np.linspace(np.round(x_min,1),np.round(x_max,1), resolution), np.linspace(np.round(y_min,1), np.round(y_max,1), resolution))
    
    #Interpolate between these points
    grid_interpolated = griddata([x,y], z, (xmesh, ymesh), method='linear')