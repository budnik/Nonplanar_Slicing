# This file creates a Mesh for the top Surface of the stl File
from scipy.interpolate import griddata
import numpy as np
from numpy import linalg
from scipy.spatial import ConvexHull, convex_hull_plot_2d, Delaunay
import matplotlib.pyplot as plt



## Input:   Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
           # maximum of the possible angle for the surface, here between the surface and the horizontal plane

## Use:     Calculates the angle between every normalvector and the horizontal plane

## Output:  gives back 3 Columnvectors: 2 coordinates with the corresponding z value

def create_surface(stl_triangles, max_angle):
    #to be programmed ----------------------
    u = stl_triangles[:,0:3]                        # Create an Array with the normalvector values

    c = u[:,2] / np.linalg.norm(u, axis=1)          # -> cosine of the angle
    calc_angle = np.arccos(np.clip(c, -1, 1))       # Calculate the angle between the 2 vectors

    filtered_array = np.delete(stl_triangles[:,3:], np.where(calc_angle > max_angle)[0], axis=0) # deletes all Indexes in the main Array where the angles > max_angle
    surface_points = np.concatenate([filtered_array[:, 0:3], filtered_array[:, 3:6], filtered_array[:, 6:9]], axis=0) # convert all points into 1 array
    surface_filtered = np.unique(surface_points, axis=0) # Delete every duplicate point in the array
    
    ##  surface_filtered contains x,y,z points of the surface
    #   surface_filtered[x, y, z]
    
    return surface_filtered



## Input:  points_to_interpolate       -> give the wanted interpolated Points in an [n,2] numpy Array
#          reference_points            -> the given datapoints of the Surface [n, (x,y,z)]
#          Method to interpolate       -> {‘linear’, ‘nearest’, ‘cubic’}

## Use:    Interpolation of the given Points of the Surface with finite Points

## Output: 1 Numpy Array with the interpolated z values and the Shape [n,1] 

def interpolate_grid(points_to_interpolate, reference_points, method_interpol = 'linear'):
       
    # Create the interpolated grid
    z_interpol = griddata(reference_points[:,:2], reference_points[:,2], (points_to_interpolate[:,0], points_to_interpolate[:,1]), method_interpol)
    return z_interpol


## Input:   surface_data                -> the given surface points with shape = [n,3] and the 3 column are (x,y,z)

## Use:     once calculation of the gradient for extrusion compensation

## Output:  
    
    
def create_gradient(surface_data):
   
    x_min = np.min(surface_data[:,0])
    x_max = np.max(surface_data[:,0])
    y_min = np.min(surface_data[:,1])
    y_max = np.max(surface_data[:,1])
    z_min = np.min(surface_data[:,2])
    z_max = np.max(surface_data[:,2])
   
    Xmesh, Ymesh = np.meshgrid(np.arange(round(x_min, 1), round(x_max, 1), 0.1), np.arange(round(y_min, 1), round(y_max, 1), 0.1))

    # Verwende griddata für die Interpolation
    Zmesh = griddata((surface_data[:,0], surface_data[:,1]), surface_data[:,2], (Xmesh, Ymesh), method='cubic')

    # Berechne die Gradienten
    GradX, GradY = np.gradient(Zmesh)
    GradZ = np.sqrt(GradX**2 + GradY**2)
    GradZ[np.isnan(GradZ)] = 0
    return Xmesh, Ymesh, GradZ

## Input:  Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] 

## Use:    Calculates the 2d outline from an object

## Output:  Points of the Outline only -> points inside are not included
#           2 Vectors with the Shape [n,1] for the x and y Values of the Outline


    
def outline_detect(stl_triangles):
    # set z values to 0 from all points
    stl_triangles[:, [5, 8, 11]] = 0
    # Connect all Points to one big Array with shape [n,3]
    reduced_array = np.concatenate([stl_triangles[:, 3:5], stl_triangles[:, 6:8], stl_triangles[:, 9:11]], axis=0)
    # delete all points that are more than once in the array
    points = np.unique(reduced_array, axis=0)
    # create a convex hull with the given points
    hull = ConvexHull(points)
    # visualize the current outline detection -> uncomment later if anoying!
    #convex_hull_plot_2d(hull)   # just to visualize the convex shape that is created
    # return 2 vectors with the x and y values of the detected outline
    return points[hull.vertices,0], points[hull.vertices,1]


