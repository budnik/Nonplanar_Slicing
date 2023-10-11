import filereader as fr
import prusa_slicer as ps
import os

if __name__ == "__main__":
    orig_stl_path = 'test_files/test_pa_outline_fein_2.stl'
    prusa_config_path = 'test_files/generic_config.ini'
    orig_stl = fr.openSTL(orig_stl_path)
    temp_stl_path = fr.writeSTL(fr.genBlock(orig_stl,10))
    ps.sliceSTL(temp_stl_path,prusa_config_path,'')
    os.remove(temp_stl_path)
