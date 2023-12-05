import numpy as np
import scipy
import os
import surface as sf
from filereader import gcode_dtype
import filereader as fr


# Calculates the area of a triangle in 3d-space
# ----------------------------------------
# Input: Numpy array  = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the triangle to be caclulated
# Output: scalar number of the area of the triangle
def triangle_area(triangle: 'np.ndarray'):
    a = np.linalg.norm(triangle[3:6]-triangle[6:9])
    b = np.linalg.norm(triangle[6:9]-triangle[9:12])
    c = np.linalg.norm(triangle[9:12]-triangle[3:6])
    s = (a + b + c) / 2
    # calculate the area
    area = np.sqrt(s*(s-a)*(s-b)*(s-c))
    return area

# Transforms a given stl file down, so that the top of the part is plane
# ----------------------------------------
# Input: STL-File np.ndarray, Filtered-Surface np.ndarray, method=[interpolate,mirror]
# Output: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the new stl
def projectSTL(stl_data: 'np.ndarray', filtered_surface: 'np.ndarray',planarBaseOffset: 'float', method='interpolate'):
    print("Transforming...")
    if(method=='interpolate'):
        stl_normals = stl_data[:,:3].copy() #save normals
        stl_data = stl_data[:,3:].copy() #copy into new array
        stl_data = stl_data.reshape(-1,3) #reshape to treat as one vector
        height_interpolated = sf.interpolate_grid(stl_data[:,:2],filtered_surface,method_interpol='cubic') #cubic interpolation, generates some NaNs however
        height_interpolated_nearest = sf.interpolate_grid(stl_data[:,:2],filtered_surface,method_interpol='nearest') #nearest method to get rid of the NaNs
        height_interpolated_nearest = scipy.ndimage.gaussian_filter(height_interpolated_nearest, sigma=4)
        height_interpolated[np.isnan(height_interpolated)] = height_interpolated_nearest[np.isnan(height_interpolated)] #replace all nans from cubic interpolation with nearest value

        stl_data[:,2] -= height_interpolated #shift interpolated  data down by some the z height at a certain point
        #stl_data[:,2] += np.min(stl_data[:,2]) #shift everything up so it sits on the z=0 plane
        stl_data = stl_data.reshape(-1,9) #reshape into array that can be written into STL
        stl_data = np.concatenate((stl_normals,stl_data),axis=1) #concatenate both arrays together
        offset_id = np.less_equal(np.abs(stl_data[:,[5,8,11]]),1e-4)
        offset = np.zeros_like(offset_id,dtype=float)
        offset[offset_id] = planarBaseOffset
        stl_data[:,[5,8,11]] -= offset
        return stl_data

    elif(method=='mirror'):
        stl_data[:,:3] = 0
        stl_data[:,[5,8,11]] = stl_data[:,[5,8,11]] * -1
        offset_id = np.less_equal(np.abs(stl_data[:,[5,8,11]]),1e-4)
        offset = np.zeros_like(offset_id,dtype=float)
        offset[offset_id] = planarBaseOffset
        stl_data[:,[5,8,11]] -= offset
        return stl_data
    else:
        raise ValueError("Method mus be \"interpolate\" or \"mirror\"")

def transformGCODE(gcode_data: 'gcode_dtype', planar_base_gcode: 'gcode_dtype', stl_path: 'str', planarBaseOffset: 'float', filtered_surface: 'np.ndarray', prusa_generated_config, layerHeight: 'float',):
    #initializing gcode writer
    gcode_file = gcode_writer('temp_gcode.gcode')
    #resetting initial values of variables
    z_lowest = 0
    x = 0
    y = 0
    z = 0
    #looping trhough each line of gcode_data and splitting it up into 1mm steps
    for j, row in enumerate(gcode_data):
        if(row['Instruction'] != 'G1'):
            gcode_file.set_line(*row)
        else:
            x_old = x
            y_old = y
            z_old = z
            if ~np.isnan(row['X']): x = row['X'] 
            if ~np.isnan(row['Y']): y = row['Y'] 
            if ~np.isnan(row['Z']): z = row['Z'] 
            length = np.round(np.sqrt((x-x_old)**2 + (y-y_old)**2 + (z-z_old)**2),decimals=0)
            f_new = row['F']
            if (length<1.0):
                gcode_file.set_line('G1',np.nan,np.nan,np.nan,row['E'],row['F']) if(x==y==z==0) else gcode_file.set_line('G1',x,y,z,row['E'],row['F'])
            elif((row['E'] != np.nan) and (row['E'] >= 0)):
                e_new = row['E']/length
            elif(row['E'] == np.nan):
                e_new = np.nan
            else:
                e_new = row['E']
            for i in range(1,int(length)+1):
                x_new = x_old + (x-x_old)/length*i
                y_new = y_old + (y-y_old)/length*i
                z_new = z_old + (z-z_old)/length*i
                if z_new < 0 : z_new = 0
                gcode_file.set_line('G1',x_new,y_new,z_new,e_new,f_new)
    #stopping gcode writer and temporarily save everything to disk
    gcode_file.flush()
    gcode_file.set_config(prusa_generated_config)
    gcode_file.stop()

    #reopening it and offsetting the height for every step
    gcode_temp = fr.openGCODE_keepcoms('temp_gcode.gcode', get_config=False)
    zTrans = scipy.interpolate.griddata(filtered_surface[:,:2], filtered_surface[:,2], (gcode_temp['X'][~np.isnan(gcode_temp['Z'])], gcode_temp['Y'][~np.isnan(gcode_temp['Z'])]), 'cubic')
    zTrans[np.isnan(zTrans)] = scipy.interpolate.griddata(filtered_surface[:,:2], filtered_surface[:,2], (gcode_temp['X'][~np.isnan(gcode_temp['Z'])][np.isnan(zTrans)], gcode_temp['Y'][~np.isnan(gcode_temp['Z'])][np.isnan(zTrans)]), 'nearest')
    gcode_temp['Z'][~np.isnan(gcode_temp['Z'])] += zTrans
    
    #get everything back down to z=0
    z_lowest = np.min(gcode_temp['Z'][~(np.logical_or(np.isnan(gcode_temp['E']),0 > gcode_temp['E']))])
    print('lowest z = ', z_lowest)
    gcode_temp['Z'] = gcode_temp['Z'] - z_lowest + planarBaseOffset
    
    #create an array that is true after the comment ;TYPE=Ironing occured
    ironing = (gcode_temp['Instruction'] == ';TYPE:Ironing')
    if (~np.all(ironing == False)):
        ironing = np.pad(np.trim_zeros(ironing,trim='b'),pad_width=(0,len(ironing)-len(np.trim_zeros(ironing,trim='b'))),mode='edge')
        
        #add ironing offset
        gradX, gradY, gradZ = sf.create_gradient(filtered_surface)
        points = np.concatenate(([gradX.flatten()],[gradY.flatten()]),axis=0)
        values = gradZ.flatten()

        gradZinterpolated = scipy.interpolate.griddata(points.T,values,(gcode_temp['X'][ironing][~np.isnan(gcode_temp['Z'][ironing])],gcode_temp['Y'][ironing][~np.isnan(gcode_temp['Z'][ironing])]),method='cubic')
        
        #funktioniert noch nicht, z höhe bleibt an enstscheidenden stellen Gleich
        dn = 0.4
        df = 0.5
        dg = 0.5*dn+df
        zcorr = dg*gradZinterpolated
        gcode_temp['Z'][ironing][~np.isnan(gcode_temp['Z'][ironing])] += zcorr**1.5 + 0.05
    
    #inserting the planar base layer before the first ;LAYER_CHANGE keyword
    gcode_temp = fr.insertBaseLayers(gcode_temp, planar_base_gcode)

    #writing the final gcode file to disk
    gcode_file2 = gcode_writer(stl_path)
    for line in gcode_temp:
        gcode_file2.set_line(*line)
    gcode_file2.flush()
    gcode_file2.set_config(prusa_generated_config)
    gcode_file2.stop()

# CLASS: has an array of gcode lines with a settable batch size, that can be written to, the array gets written to gcode file on disk every time it is full
# initialization: path: string of the path of the written gcode file, batch_size: size of the temporary array that saves the gcode lines (default 500), creates a file at the specified path, overwrites it in case it already exists
# method set_line: takes a gcode line of type gcode_dtype and saves it to the temporary array, flushes if the temporary array is full
# method set_config: takes a slicer_config object and writes the config string at to the file on disk
# method flush: writes the temporary array to disk, even if it is not full
# method stop: closes the file
class gcode_writer:
    def __init__(self, path, batch_size = 500):
        self.batchsize = batch_size
        self.path = path.rsplit('.')[0] + '.gcode'
        try:
            self.f = open(self.path,'x')
        except FileExistsError:
            os.remove(self.path)
            self.f = open(self.path,'x')
        except Exception as e:
            raise e
        self.lines = np.empty(batch_size, dtype=gcode_dtype)
        self.currline = 0

    def set_line(self, instruction = '',x=np.nan,y=np.nan,z=np.nan,e=np.nan,f=np.nan):
        self.lines[self.currline] = instruction,x,y,z,e,f
        self.currline += 1
        if(self.currline >= self.batchsize):
            self.flush()

    def set_config(self, comment):
        self.f.write(comment)

    def flush(self):
        for line in self.lines[0:self.currline]:
            if line['Instruction'] == 'G1':
                X = '' if np.isnan(line['X']) else (' X' + str(np.round(line['X'],4)))
                Y = '' if np.isnan(line['Y']) else (' Y' + str(np.round(line['Y'],4)))
                Z = '' if np.isnan(line['Z']) else (' Z' + str(np.round(line['Z'],4)))
                E = '' if np.isnan(line['E']) else (' E' + str(np.round(line['E'],4)))
                F = '' if np.isnan(line['F']) else (' F' + str(np.round(line['F'],0)))
                self.f.write(f"G1{X}{Y}{Z}{E}{F}\n")
                pass
            else:
                self.f.write(str(line['Instruction'] + '\n'))
                pass
        self.currline = 0

    def stop(self):
        self.f.close()