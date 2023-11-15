import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import gcode_transform_1 as gc1
import os
import transform as tf

if __name__ == "__main__":
    orig_stl_path = 'test_files/test_slope_pa_2.stl'
    prusa_config_path = 'test_files/generic_config_Deltiq2_ironing.ini'
    debug=True
    numPlanarBaseLayers = 2

    orig_stl = fr.openSTL(orig_stl_path)
    upscaled_stl = sf.upscale_stl(orig_stl, 3)
    filtered_surface, limits = sf.create_surface(upscaled_stl,np.deg2rad(80))
    z_mean = np.average(filtered_surface[:,2])

    print('Fall 2')
    ini_config = fr.slicer_config(fr.openINI(prusa_config_path))
    layer_height = ini_config.get_config_param('layer_height')
    planarBaseOffset = numPlanarBaseLayers * float(layer_height)

    ps.sliceSTL(orig_stl_path,prusa_config_path,'--skirts 2 --skirt-height 2 --skirt-distance 6','C:\Program Files\Prusa3D\PrusaSlicer')
    planar_base_gcode, prusa_generated_config_planar = fr.openGCODE_keepcoms('output.gcode')
    base_layer_gcode = fr.readBaseLayers(planar_base_gcode,numPlanarBaseLayers)

    transformed_stl = tf.projectSTL(stl_data=upscaled_stl,filtered_surface=filtered_surface,planarBaseOffset=0.0,method='interpolate',resolution = 2)
    temp_stl_path = fr.writeSTL(transformed_stl)

    ps.repairSTL(temp_stl_path)
    ps.sliceSTL(temp_stl_path,prusa_config_path,'','C:\Program Files\Prusa3D\PrusaSlicer')
    planar_gcode, prusa_generated_config = fr.openGCODE_keepcoms('output.gcode')
    tf.transformGCODE(planar_gcode, base_layer_gcode, orig_stl_path, planarBaseOffset,filtered_surface, prusa_generated_config, layer_height)
    
    if debug==False:
        os.remove(temp_stl_path)
        os.remove('output.gcode')
        os.remove('temp_gcode.gcode')


