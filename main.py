import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import os

if __name__ == "__main__":
    orig_stl_path = 'Welle.stl'
    prusa_config_path = 'test_files/generic_config.ini'
    orig_stl = fr.openSTL(orig_stl_path)
    filtered_surface = sf.create_surface(orig_stl,np.deg2rad(45))
    z_mean = np.average(filtered_surface[:,2])
    temp_stl_path = fr.writeSTL(fr.genBlock(orig_stl,z_mean))
    ps.sliceSTL(temp_stl_path,prusa_config_path,'--info')
    #os.remove(temp_stl_path)