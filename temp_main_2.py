import filereader
import numpy as np


path_gcode = "C:/Users/zuerc/Documents/Informatik_Projekte/PA/PA23_wuem_346_Nonplanar/Scheibe.gcode"
gcode_raw = filereader.openGCODE(path_gcode)
"""
print(gcode_raw.shape[0])
print(gcode_raw.dtype)
print(gcode_raw["X"])
"""
my_list = []

# Vektoren erstellen und zur Liste hinzufgen
vector_X = [1.0, 2.0, 3.0]
vector_Y = [4.0, 5.0, 6.0]
vector_Z = [7.0, 8.0, 9.0]
vector_E = [10.0, 11.0, 12.0]
vector_F = [13, 14, 15]

my_list.append((vector_X, vector_Y, vector_Z, vector_E, vector_F))

# Einen weiteren Satz von Vektoren hinzufen
vector_X = [16.0, 17.0, 18.0]
vector_Y = [19.0, 20.0, 21.0]
vector_Z = [22.0, 23.0, 24.0]
vector_E = [25.0, 26.0, 27.0]
vector_F = [28, 29, 30]

my_list.append((vector_X, vector_Y, vector_Z, vector_E, vector_F))

# Die Liste in ein NumPy-Array umwandeln
dtype = [('X', '<f8'), ('Y', '<f8'), ('Z', '<f8'), ('E', '<f8'), ('F', '<i4')]

my_array = np.array(my_list, dtype=dtype)
print(my_array)

    
    
