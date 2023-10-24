import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import os
import transform as tf

if __name__ == "__main__":
    orig_stl_path = 'Welle.stl'
    prusa_config_path = 'test_files/generic_config.ini'
    orig_stl = fr.openSTL(orig_stl_path)
    filtered_surface = sf.create_surface(orig_stl,np.deg2rad(45))
    z_mean = np.average(filtered_surface[:,2])
    transformed_stl = tf.projectSTL(orig_stl,filtered_surface,method='mirror')
    temp_stl_path = fr.writeSTL(transformed_stl)
    ps.sliceSTL(temp_stl_path,prusa_config_path,'--info')
    ps.repairSTL(temp_stl_path)
    os.remove(temp_stl_path)
    planar_gcode = fr.openGCODE('output.gcode')
    #tf.transformGCODE(planar_gcode, orig_stl_path, filtered_surface)
    
