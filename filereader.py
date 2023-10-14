# Imports:
from io import TextIOWrapper
import struct
import time
import numpy as np
import mmap
import os
from stl import mesh
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay

# Opens, verifies and parses a given stl-file
# ----------------------------------------
# Input: STL-File path (string)
# Output: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
def openSTL(path: 'str'):
    file_path = path
    # Creating exception classes to store correct info
    class STLFormatError(Exception):
        def __init__(self, line, expected = None, *args):
            super().__init__(args)
            self.line = line
            self.expected = expected

        def __str__(self):
            if self.line == -1 and self.expected == None:
                return 'STL-Format error. Binary file length does not match in-file specification.'
            else:
                return f'STL-Format error in line {self.line}. Expected {self.expected}. File does not comply with STL format standards.'   
    class STLEndingError(Exception):
        def __init__(self, line, *args):
            super().__init__(args)
            self.line = line

        def __str__(self):
            return f'STL-Format error in line {self.line}. File ends unexpectedly. File does not comply with STL format standards.'

    def checkParseAsciiSTL(file: 'TextIOWrapper'): #validates and parses an ASCII-STL

        lines = 0               #counting the number of lines in the STL
        curr_triangle = 1
        for line in file:
            lines += 1

        num_triangles = int((lines-2)/7) #each triangle has info on 7 lines

        triangles = np.zeros([num_triangles,12],dtype=float) #initializing array 

        linenr = 1
        file.seek(0)
        if file.readline().rsplit(' ')[0] != ('solid'):  #STLs start with solid 'NAME'
            raise STLFormatError(linenr, '"solid NAME"')

        while True:
            line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
            if line == ['']:
                raise STLEndingError(linenr)
            if line[0] == 'endsolid':
                break
            linenr += 1
            if line[0:2] != ['facet','normal'] or len(line[2:]) != 3:
                raise STLFormatError(linenr, '"facet normal X Y Z"')
            try:
                triangles[curr_triangle-1,0:3] = line[2:]
            except ValueError:
                print('Normal Vector Values are not formatted Correctly. Error in STL-Line ' + str(linenr))
            
            line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
            if line == ['']:
                raise STLEndingError('File ends abruptly in STL-Line ' + str(linenr))
            linenr += 1
            if line[0:2] != ['outer','loop']:
                raise STLFormatError(linenr,'"outer loop"')

            for i in range(3):
                line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
                if line == ['']:
                    raise STLEndingError('File ends abruptly in STL-Line ' + str(linenr))
                linenr += 1
                if line[0:1] != ['vertex'] or len(line[1:]) != 3:
                    raise STLFormatError(linenr,'"vertex X Y Z"')
                try:
                    triangles[curr_triangle-1,3+3*i:6+3*i] = line[1:]
                except ValueError:
                    print('Vertex not formatted correctly. Error in STL-Line ' + str(linenr))
            
            line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
            if line == ['']:
                raise STLEndingError('File ends abruptly in STL-Line ' + str(linenr))
            linenr += 1
            if line != ['endloop']:
                raise STLFormatError(linenr,'"endloop"')
            
            line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
            if line == ['']:
                raise STLEndingError(linenr)
            linenr += 1
            if line != ['endfacet']:
                raise STLFormatError(linenr,'"endfacet"')
            curr_triangle += 1
        return triangles

    def checkParseBinSTL(file: 'TextIOWrapper'): #validates and parses a Binary-STL
        file.seek(80) 
        num_triangles = struct.unpack('<i',file.read(4))[0] #reads the 32bit int stating the number of triangles 
        file.read()
        if file.tell() != (80+4+50*num_triangles): #if the file length doesnt match up with the specified number of triangles, raises an error
            raise STLFormatError(-1)
        file.seek(0) #resets the file position
        triangles = np.fromfile(file,dtype=[('TriangleData','12<f4'),('AttributeByteCount','<u2')],offset=84)['TriangleData'].astype(float) #parsing the stl file via numpy, getting rid of Attribute Byte Count
        return triangles


    if file_path.endswith('.stl'): #Check if the given File is of Filetype STL
        try:
            bin_file = open(file_path,'rb') #opens File in Binary-Read-Mode
            if (bin_file.read(6).decode('ascii')) == ('solid '): #if it starts with 'solid ' it is most likely an ASCII format STL File
                print('Found ASCII File at:', file_path)
                #isAscii = True
                bin_file.close()                #reopens File in ASCII read mode
                ascii_file = open(file_path,'r')    #reopens File in ASCII read mode
                triangles = checkParseAsciiSTL(ascii_file)
                ascii_file.close()
                print('ASCII file valid at:', file_path)
                return triangles
            else:
                print('Found Binary File at:', file_path)
                #isBinary = True
                triangles = checkParseBinSTL(bin_file)
                print('Binary file valid at:', file_path)
                bin_file.close()
                return triangles
        except OSError as e:
            print(e)
        except STLEndingError as e:
            print(e)
        except STLFormatError as e:
            print(e)
        except Exception as e:
            print('Unexpected Error while reading file')
            print(e)
        finally:
            bin_file.close()
    else:
        print(file_path, 'is not an STL File')

# Writes a valid STL-File to pass to the slicer
# ----------------------------------------
# Input: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
# Output: path of the written STL-File
def writeSTL(triangles: 'np.ndarray[np.float]'):
    path = 'temp_slicing_'+time.strftime('%d%m%Y_%H%M%S', time.localtime())+'.stl'
    file = open(path,'xb')
    file.write(b' '.ljust(80))
    num_triangles = len(triangles[:,0])
    file.write(struct.pack('<i',num_triangles))
    for triangle in triangles:
        file.write(struct.pack('<12f',*triangle))
        file.write(b'  ')
    file.close()
    print('Written', num_triangles,'triangles')
    return path

# recognizes the outline of a flat stl-surface
# ----------------------------------------
# Input: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the base of an STL or a whole STL 
# Output: Numpy array of shape [NUMBER_TRIANGLES,12 with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the newly generated block STL that is flat and has height z_mean
def genBlock(stl_triangles: 'np.ndarray[np.float]', z_mean: 'np.float'):
    #z_min = np.min(stl_triangles[:,[5,8,11]])
    #stl_triangles[:,[5,8,11]] -= z_min
    testarr = ~np.bitwise_and.reduce((np.isclose(stl_triangles[:,5::3],np.zeros_like(stl_triangles[:,5::3]),1e-17)),axis=1) #detects lines where z is sufficiently close to 0
    base_triangles = np.delete(stl_triangles,testarr,axis=0) #gets rid of all lines where z is not within a specified tolerance to 0
    top_triangles = base_triangles.copy()
    top_triangles[:,2] *= -1
    base_triangles[:,[5,8,11]] = 0
    top_triangles[:,[5,8,11]] = z_mean

    triangles_check = np.concatenate((base_triangles[:,[3,4,6,7]],base_triangles[:,[6,7,9,10]],base_triangles[:,[3,4,9,10]]),axis=0)
    triangles_check = np.concatenate((triangles_check,triangles_check[:, [2, 3, 0, 1]]))

    uniq,idx,count= np.unique(triangles_check,return_index=True,return_counts=True,axis=0)
    count = count[idx.argsort()]
    uniq = uniq[idx.argsort()]
    uniq = uniq[np.logical_not((count-1).astype(bool))]
    uniq = uniq[:len(uniq)//2]
    sides = np.zeros((2*len(uniq[:,0]),12))
    sides[:,11] = z_mean
    sides[len(uniq[:,0]):,8] = z_mean
    sides[len(uniq[:,0]):,[3,4,6,7]] = uniq
    sides[len(uniq[:,0]):,[9,10]] = uniq[:,0:2]
    sides[:len(uniq[:,0]),[6,7,9,10]] = uniq
    sides[:len(uniq[:,0]),[3,4]] = uniq[:,2:]
    flat_stl = np.concatenate((base_triangles,top_triangles,sides),axis=0)
    flat_stl[:,0:3] = 0
    print('Generated Block STL Data with', len(flat_stl[:,0]), 'triangles')
    return flat_stl
    #return uniq, triangles_check

# Opens, verifies and parses a given stl-file
# ----------------------------------------
# Input: STL-File path (string)
# Output: None
def openSTL_lib(path):
    your_mesh = mesh.Mesh.from_file(path)

# Opens, verifies and parses a given GCODE-file
# ----------------------------------------
# Input: GCODE-File path (string), reading mode (mmap, manual, None) 
# Output: [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
def openGCODE(path: 'str',mode='mmap'):

    with open(path,'r') as file: # checks length of file to estimate array size to allocate
        lines = 0
        for line in file:
            lines += 1
    gcode_arr = np.full(lines,np.nan,dtype=[('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','f8')]) #initializes an array of NaN's with a custom datatype, i.o. to acces each value by name
    if (mode=='mmap'):
        with open(path,'r') as f:  #opening file with context manager
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm: #initializes file memory mapping
                line_list = []
                line_nr = 0 
                while line_nr<lines:
                    line_list = mm.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ') #reads next line and gets rid of extra characters and comments, puts it in a list
                    if line_list[0] == b'G1':  #if the current line is a moving line
                        gcode_arr[line_nr]['Instruction'] = 'G1'
                        for single_inst in line_list[1:]: #for loop through the entries of every line
                            gcode_arr[line_nr][chr(single_inst[0])] = single_inst[1:] #puts it in the corresponding field
                    else:
                        gcode_arr[line_nr]['Instruction'] = (b' '.join(line_list)).decode('utf-8')
                    line_nr += 1 #counts actual amount of moving lines
        return gcode_arr

    if (mode=='manual'):
        with open(path,'rb') as f:  #opening file with context manager
            line_list = f.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
            line_nr = 0
            while line_nr<lines:
                line_list = f.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
                if line_list[0] == b'G1':  #if the current line is a moving line
                    gcode_arr[line_nr]['Instruction'] = 'G1'
                    for single_inst in line_list[1:]: #for loop through the entries of every line
                        gcode_arr[line_nr][chr(single_inst[0])] = single_inst[1:] #puts it in the corresponding field
                else:
                    gcode_arr[line_nr]['Instruction'] = (b' '.join(line_list)).decode('utf-8')
                line_nr += 1 #counts actual amount of moving lines
        return gcode_arr

    if (mode !='mmap' and mode !='manual'):
        raise ValueError("Unsupported parsing mode '"+mode+"'. Use 'mmap' or 'manual'.")

# Testing Code:
if __name__ == "__main__":     
    path_stl_ascii = 'Scheibe.stl' #Filename definition
    path_gcode = 'Scheibe.gcode' #filename definition
    path_stl_bin = 'Scheibe_bin.stl' #filename definition

    start = time.time()
    openSTL(path_stl_ascii)
    end = time.time()
    print('ASCII time:', end-start, 's')

    start = time.time()
    openSTL_lib(path_stl_ascii)
    end = time.time()
    print('ASCII library time:', end-start, 's')

    start = time.time()
    openSTL(path_stl_bin)
    end = time.time()
    print('Binary time:', end-start, 's')

    start = time.time()
    openSTL_lib(path_stl_bin)
    end = time.time()
    print('Binary library time:', end-start, 's')

    start = time.time()
    openGCODE(path_gcode,mode='mmap')
    end = time.time()
    print('Memory mapped time:', end-start, 's')

    start = time.time()
    openGCODE(path_gcode,mode='manual')
    end = time.time()
    print('Normal file handling time:', end-start, 's')

    stl_triangles = openSTL('test_pa_outline_fein_2.stl')
    start = time.time()
    flat_points = genBlock(stl_triangles,10)
    end = time.time()
    writeSTL(flat_points)
    print('Baseline handling time:', end-start, 's')
    
    