from io import TextIOWrapper

class STLFormatError(Exception):
    def __init__(self, line, expected, *args):
        super().__init__(args)
        self.line = line
        self.expected = expected

    def __str__(self):
        return f'STL-Format error in line {self.line}. Expected {self.expected}. File does not comply with STL format standards.'   
class STLEndingError(Exception):
    def __init__(self, line, *args):
        super().__init__(args)
        self.line = line

    def __str__(self):
        return f'STL-Format error in line {self.line}. File ends unexpectedly. File does not comply with STL format standards.'

def checkAsciiSTL(file: 'TextIOWrapper'):
    EOFFlag = 0
    linenr = 1
    file.seek(0)
    if file.readline().rsplit(' ')[0] != ('solid'):
        raise STLFormatError(linenr, '"solid NAME"')

    while True:
        line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
        if line == ['']:
            raise STLEndingError('File ends abruptly in STL-Line ' + str(linenr))
        if line[0] == 'endsolid':
            break
        linenr += 1
        if line[0:2] != ['facet','normal'] or len(line[2:]) != 3:
            raise STLFormatError(linenr, '"facet normal X Y Z"')
        try:
            list(map(float, line[2:]))
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
                list(map(float, line[1:]))
            except ValueError:
                print('Vertex not formatted correctly. Error in STL-Line ' + str(linenr))
        
        line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
        if line == ['']:
            raise STLEndingError('File ends abruptly in STL-Line ' + str(linenr))
        linenr += 1
        if line[0:2] != ['endloop']:
            raise STLFormatError(linenr,'"endloop"')
        
        line = " ".join(file.readline().strip().replace('\n','').replace('\t','').split()).rsplit(' ')
        if line == ['']:
            raise STLEndingError(linenr)
        linenr += 1
        if line[0:2] != ['endfacet']:
            raise STLFormatError(linenr,'"endfacet"')


    

file_path = 'PA23_wuem_346_Nonplanar/test_stl_ascii.stl' #Filename definition
if file_path.endswith('.stl'): #Check if the given File is of Filetype STL
    try:
        unknown_file = open(file_path,'rb') #opens File in Binary-Read-Mode
        if (unknown_file.read(6).decode('ascii')) == ('solid '): #if it starts with 'solid ' it is most likely an ASCII format STL File
            print("Found ASCII File at:", file_path)
            isAscii = True
            unknown_file.close()                #reopens File in ASCII read mode
            ascii_file = open(file_path,'r')    #reopens File in ASCII read mode
            checkAsciiSTL(ascii_file)
            ascii_file.close()
            print('ASCII file valid at:', file_path)
        else:
            isBinary = True
            print("Found Binary File at:", file_path)
            unknown_file.close()
    except OSError:
        print("File not found at:", file_path)
    except STLEndingError as e:
        print(e)
    except STLFormatError as e:
        print(e)
    except Exception as e:
        print("Unexpected Error while reading file")
        print(e)
else:
    print(file_path, 'is not an STL File')

