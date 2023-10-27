import numpy as np
import scipy
import matplotlib.pyplot as plt
import os
import surface as sf
from filereader import gcode_dtype
import filereader as fr


# Transforms a given stl file down, so that the top of the part is plane
# ----------------------------------------
# Input: STL-File np.ndarray, Filtered-Surface np.ndarray, method=[interpolate,mirror]
# Output: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the new stl
def projectSTL(stl_data: 'np.ndarray', filtered_surface: 'np.ndarray', method='interpolate'):
    if(method=='interpolate'):
        stl_normals = stl_data[:,:3].copy() #save normals
        stl_data = stl_data[:,3:].copy() #copy into new array
        stl_data = stl_data.reshape(-1,3) #reshape to treat as one vector
        height_interpolated = sf.interpolate_grid(stl_data[:,:2],filtered_surface,method_interpol='cubic') #cubic interpolation, generates some NaNs however
        height_interpolated_nearest = sf.interpolate_grid(stl_data[:,:2],filtered_surface,method_interpol='nearest') #nearest method to get rid of the NaNs
        height_interpolated[np.isnan(height_interpolated)] = height_interpolated_nearest[np.isnan(height_interpolated)] #replace all nans from cubic interpolation with nearest value
        stl_data[:,2] -= height_interpolated #shift interpolated  data down by some the z height at a certain point
        stl_data[:,2] += np.min(stl_data[:,2]) #shift everything up so it sits on the z=0 plane
        stl_data = stl_data.reshape(-1,9) #reshape into array that can be written into STL
        stl_data = np.concatenate((stl_normals,stl_data),axis=1) #concatenate both arrays together
        return stl_data

    elif(method=='mirror'):
        stl_data[:,:3] = 0
        stl_data[:,[5,8,11]] = stl_data[:,[5,8,11]] * -1
        stl_data[:,[5,8,11]] += np.min(stl_data[:,[5,8,11]])
        return stl_data
    else:
        raise ValueError("Method mus be \"interpolate\" or \"mirror\"")

def transformGCODE(gcode_data: 'gcode_dtype',stl_path: 'str', filtered_surface: 'np.ndarray', prusa_generated_config):
    gcode_file = gcode_writer('temp_gcode.gcode')
    z_lowest = 0
    x = 0
    y = 0
    z = 0
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
            if (length != 0 and row['E'] != np.nan):
                e_new = row['E']/length
            elif (length<1.0):
                gcode_file.set_line('G1',x,y,z,row['E'],row['F'])
            elif row['E'] == np.nan:
                e_new = np.nan
            else:
                e_new = row['E']
            for i in range(1,int(length)+1):
                x_new = x_old + (x-x_old)/length*i
                y_new = y_old + (y-y_old)/length*i
                z_new = z_old + (z-z_old)/length*i
                if z_new < 0 : z_new = 0
                gcode_file.set_line('G1',x_new,y_new,z_new,e_new,f_new)
        row_old = row
    gcode_file.flush()
    gcode_file.stop()

    layer_height = 0.2

    gcode_file2 = gcode_writer(stl_path)
    gcode_temp = fr.openGCODE_keepcoms('temp_gcode.gcode', get_config=False)
    gcode_temp['Z'][~np.isnan(gcode_temp['Z'])] = gcode_temp['Z'][~np.isnan(gcode_temp['Z'])] + scipy.interpolate.griddata(filtered_surface[:,:2], filtered_surface[:,2], (gcode_temp['X'][~np.isnan(gcode_temp['Z'])], gcode_temp['Y'][~np.isnan(gcode_temp['Z'])]), 'linear', fill_value = np.inf)
    gcode_temp['Z'][np.isinf(gcode_temp['Z'])] = gcode_temp['Z'][np.isinf(gcode_temp['Z'])] + scipy.interpolate.griddata(filtered_surface[:,:2], filtered_surface[:,2], (gcode_temp['X'][np.isinf(gcode_temp['Z'])], gcode_temp['Y'][np.isinf(gcode_temp['Z'])]), 'nearest')
    z_lowest = np.min(gcode_temp['Z'][~np.isnan(gcode_temp['E'])])
    print('lowest z = ', z_lowest)
    gcode_temp['Z'] = gcode_temp['Z'] - z_lowest + layer_height
    #gcode_temp['E'][np.less_equal(gcode_temp['Z'],0.1)] *= 0.75
    gcode_temp['Z'][np.less_equal(gcode_temp['Z'],2*layer_height)] = layer_height
    for line in gcode_temp:
        gcode_file2.set_line(*line)
    gcode_file2.flush()
    gcode_file2.set_comm(prusa_generated_config)
    gcode_file2.stop()

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

    def set_comm(self, comment):
        try:
            self.f.write(comment.decode('utf-8') )
        except AttributeError:
            self.f.write(comment)
        except Exception as e:
            raise e

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