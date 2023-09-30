from io import TextIOWrapper
import struct
import time
import numpy as np

path = 'Scheibe.stl' #Filename definition

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

        lines = 0
        curr_triangle = 1
        for line in file:
            lines += 1

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
    else:
        print(file_path, 'is not an STL File')



start = time.time()
stl1test = openSTL(path)
end = time.time()
print('ASCII time:', end-start)

path2 = 'Scheibe_bin.stl'
start = time.time()
stl2test = openSTL(path2)
end = time.time()
print('Binary time:', end-start)

if(np.array_equal(stl1test,stl1test)):
    print("Equal")