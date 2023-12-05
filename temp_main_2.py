import filereader as fr
import numpy as np
import surface
import gcode_transform_1 as transform
import matplotlib.pyplot as plt
import prusa_slicer as ps
from mpl_toolkits.mplot3d import Axes3D

stl_pfad = "test_files/test_pa_outline_fein_2.stl"
# stl_pfad = "Welle.stl"
stl_pfad = "test_files/Welle_Radius.stl"
stl_pfad = "test_files/Sohle.stl"

ini_pfad = "test_files/generic_config_Deltiq2.ini"

triangle_array = fr.openSTL(stl_pfad)
#triangle_array = surface.upscale_stl(triangle_raw, 1)
config = fr.slicer_config(fr.openINI(ini_pfad))


# Oberflaeche, limits = surface.create_surface(triangle_array, np.deg2rad(40)) # Winkel
# points_sorted = surface.sort_contour(contour_unsorted[:,0], contour_unsorted[:,1])

# surface_filtered = surface.offset_contour(points_sorted[:,0], points_sorted[:,1], Oberflaeche, 4)
# ax.plot(points_sorted[:,0], points_sorted[:,1], 0)
# ax.scatter(uniq[:,0], uniq[:,1], 0)
# ax.scatter(surface_filtered[:,0], surface_filtered[:,1])
# ax.scatter(Oberflaeche[:,0], Oberflaeche[:,1], 1)

# plt.show()

printSetting = transform.PrintInfo(config,FullBottomLayers=4, FullTopLayers=4, resolution_zmesh = 0.05)
points_sorted = surface.sort_contour(triangle_array)
Oberflaeche, limits = surface.create_surface(triangle_array, np.deg2rad(40)) # Winkel
surface_filtered = surface.offset_contour(points_sorted[:,0], points_sorted[:,1], Oberflaeche, 5.5)
xmesh, ymesh, zmesh = surface.create_surface_extended(surface_filtered, limits, printSetting.resolution)
#ax.scatter(surface_filtered[:,0], surface_filtered[:,1], 0)
#plt.show()
gradx_mesh, grady_mesh, gradz = surface.create_gradient(Oberflaeche, limits)

transformed_stl = transform.trans_stl(triangle_array, zmesh, limits, printSetting)
stl_path = fr.writeSTL(transformed_stl)
#ps.repairSTL(stl_path)


path_gcode = "C:/Users/zuerc/Documents/Informatik_Projekte/PA/PA23_wuem_346_Nonplanar/output.gcode"
ps.sliceSTL(stl_path,ini_pfad,'--info', 'C:\Program Files\Prusa3D\PrusaSlicer')
gcode_raw, config = fr.openGCODE_keepcoms(path_gcode, get_config=True)


transform.trans_gcode(gcode_raw, gradz, zmesh, printSetting, limits, config_string=config)
