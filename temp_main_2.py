import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import transform_method_1 as tm1
import os
import transform_method_2 as tf

if __name__ == "__main__":
    orig_stl_path = 'test_files/wedge.stl'
    prusa_config_path = 'test_files/generic_config_Deltiq2_ironing.ini'
    debug=True
    numPlanarBaseLayers = 2

    ps.repairSTL(orig_stl_path)
    orig_stl = fr.openSTL(orig_stl_path)
    upscaled_stl = orig_stl
    #outline = sf.detectSortOutline(orig_stl)
    #upscaled_stl = sf.upscale_stl(orig_stl, 0)

    #filtered_surface = sf.create_surface_without_outline(upscaled_stl,np.deg2rad(89.9),0.05,outline) #usage with radius 

    
    surface, limits = sf.create_surface(upscaled_stl,np.deg2rad(80)) #usage without radius
    xmesh, ymesh, zmesh = sf.create_surface_extended(surface, limits, 0.05)
    filtered_surface = np.concatenate(([xmesh.flatten()],[ymesh.flatten()],[zmesh.flatten()]),axis=0).T



    z_mean = np.average(filtered_surface[:,2])
    #x_center = np.average(xmesh)
    #y_center = np.average(ymesh)

    print('Fall 2')
    ini_config = fr.slicer_config(fr.openINI(prusa_config_path))
    layer_height = ini_config.get_config_param('layer_height')
    planarBaseOffset = (numPlanarBaseLayers + 1) * float(layer_height)

    ps.sliceSTL(orig_stl_path,prusa_config_path,f'{"--skirts 2 --skirt-height 2 --skirt-distance 6"}','C:\Program Files\Prusa3D\PrusaSlicer')
    planar_base_gcode, prusa_generated_config_planar = fr.openGCODE_keepcoms('output.gcode')
    base_layer_gcode = fr.readBaseLayers(planar_base_gcode,numPlanarBaseLayers)
    # interpolate oder mirror in settings
    transformed_stl = tf.projectSTL(stl_data=upscaled_stl,filtered_surface=filtered_surface,planarBaseOffset=0.0,method='mirror')
    temp_stl_path = fr.writeSTL(transformed_stl)

    ps.repairSTL(temp_stl_path)
    ps.sliceSTL(temp_stl_path,prusa_config_path,'','C:\Program Files\Prusa3D\PrusaSlicer')
    planar_gcode, prusa_generated_config = fr.openGCODE_keepcoms('output.gcode')
    tf.transformGCODE(planar_gcode, base_layer_gcode, orig_stl_path, planarBaseOffset,filtered_surface, prusa_generated_config, layer_height)
    
    if debug==False:
        os.remove(temp_stl_path)
        os.remove('output.gcode')
        os.remove('temp_gcode.gcode')


# outline surface generation does not work for large files... -> use mirror and normal surface 