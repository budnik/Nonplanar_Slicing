import filereader as fr
import numpy as np
import surface
import gcode_transform_1 as transform
import matplotlib.pyplot as plt
import prusa_slicer as ps
from mpl_toolkits.mplot3d import Axes3D

stl_pfad = "test_files/test_pa_outline_fein_2.stl"
stl_pfad = "Welle.stl"
stl_pfad = "test_files/Welle_Phase.stl"
ini_pfad = "test_files/generic_config.ini"

triangle_array = fr.openSTL(stl_pfad)
config = fr.slicer_config(fr.openINI(ini_pfad))

printSetting = transform.PrintInfo(config,FullBottomLayers=4, FullTopLayers=4, resolution_zmesh = 0.02)
Oberflaeche, limits = surface.create_surface(triangle_array, np.deg2rad(40)) # Winkel
xmesh, ymesh, zmesh = surface.create_surface_extended(Oberflaeche, limits, printSetting.resolution)
transformed_stl = transform.trans_stl(triangle_array, zmesh, limits, printSetting)
stl_path = fr.writeSTL(transformed_stl)
#ps.repairSTL(stl_path)




# path_gcode = "C:/Users/zuerc/Documents/Informatik_Projekte/PA/PA23_wuem_346_Nonplanar/output.gcode"
# gcode_raw, config = fr.openGCODE_keepcoms(path_gcode, get_config=True)


# transform.trans_gcode(gcode_raw, Oberflaeche, printSetting, limits, config_string=config)
