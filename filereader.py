from io import TextIOWrapper
import struct
import time
import numpy as np
import mmap
import re

path_stl_ascii = 'Scheibe.stl' #Filename definition
path_gcode = 'Scheibe.gcode' #filename definition
path_stl_bin = 'Scheibe_bin.stl' #filename definition

# Opens, verifies and parses a given stl-file
#----------------------------------------
# Input: STL-File path (string)
# Output: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
def openSTL(path: 'str'):
    file_path = path
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

        start_ = time.time()
        lines = 0
        curr_triangle = 1
        for line in file:
            lines += 1
        end_ = time.time()
        print('Line counting: ',end_-start_)

        num_triangles = int((lines-2)/7)

        triangles = np.zeros([num_triangles,12],dtype=float)

        linenr = 1
        file.seek(0)
        if file.readline().rsplit(' ')[0] != ('solid'):
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
                isAscii = True
                bin_file.close()                #reopens File in ASCII read mode
                ascii_file = open(file_path,'r')    #reopens File in ASCII read mode
                triangles = checkParseAsciiSTL(ascii_file)
                ascii_file.close()
                print('ASCII file valid at:', file_path)
                return triangles
            else:
                print('Found Binary File at:', file_path)
                isBinary = True
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



# Opens, verifies and parses a given GCODE-file
#----------------------------------------
# Input: GCODE-File path (string)
# Output: Numpy array of shape [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
def openGCODE(path: 'str',mode='mmap'):

    with open(path,'r') as file:
        start_ = time.time()
        lines = 0
        for line in file:
            lines += 1
        end_ = time.time()
    gcode_arr = np.zeros(lines,dtype=[('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')])

    if (mode=='mmap'):
        start = time.time()
        with open(path,'r') as f:  #opening file with context manager
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                line_list = mm.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
                move_line_nr = 0
                while(not (line_list[0:2] == [b'M73',b'P100'])): #waits until the printing is complete
                    line_list = mm.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
                    if line_list[0] == b'G1':  
                        line_arr = np.zeros(1,dtype=[('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')])
                        for single_inst in line_list[1:]:
                            gcode_arr[move_line_nr][chr(single_inst[0])] = single_inst[1:]
                        move_line_nr += 1
        gcode_arr = np.resize(gcode_arr,move_line_nr)   
        end = time.time()
        print('Memory Mapped:',end-start)
        return gcode_arr

    if (mode=='manual'):
        start = time.time()
        with open(path,'rb') as f:  #opening file with context manager
            line_list = f.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
            move_line_nr = 0
            while(not (line_list[0:2] == [b'M73',b'P100'])): #waits until the printing is complete
                line_list = f.readline().replace(b'\n',b'').split(b';')[0].strip().split(b' ')
                if line_list[0] == b'G1':  
                    line_arr = np.zeros(1,dtype=[('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')])
                    for single_inst in line_list[1:]:
                        gcode_arr[move_line_nr][chr(single_inst[0])] = single_inst[1:]
                    move_line_nr += 1
        gcode_arr = np.resize(gcode_arr,move_line_nr)    
        end = time.time()
        print('Normal Read:',end-start)

    if (mode !='mmap' and mode !='manual'):
        raise ValueError("Unsupported parsing mode '"+mode+"'. Use 'mmap' or 'manual'.")

if __name__ == "__main__":
    #Testing Code:
    """
    start = time.time()
    stl1test = openSTL(path_stl_ascii)
    end = time.time()
    print('ASCII time:', end-start)

    start = time.time()
    stl2test = openSTL(path_stl_bin)
    end = time.time()
    print('Binary time:', end-start)
    """
    openGCODE(path_gcode)