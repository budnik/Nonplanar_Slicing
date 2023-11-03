# Imports:
from io import TextIOWrapper
import struct
import time
import numpy as np
import mmap
import os
from enum import Enum

gcode_dtype = np.dtype([('Instruction','<U200'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','f8')])

class slicer_config:    
    config_type = Enum('config_type', ['GCODE', 'INI'])
    options_names = ['autoemit_temperature_commands', 'avoid_crossing_curled_overhangs', 'avoid_crossing_perimeters',
                'avoid_crossing_perimeters_max_detour', 'bed_custom_model', 'bed_custom_texture', 'bed_shape',
                'bed_temperature', 'before_layer_gcode', 'between_objects_gcode', 'bottom_fill_pattern',
                'bottom_solid_layers', 'bottom_solid_min_thickness', 'bridge_acceleration', 'bridge_angle',
                'bridge_fan_speed', 'bridge_flow_ratio', 'bridge_speed', 'brim_separation', 'brim_type',
                'brim_width', 'color_change_gcode', 'compatible_printers_condition_cummulative','complete_objects',
                'cooling', 'cooling_tube_length', 'cooling_tube_retraction','default_acceleration',
                'default_filament_profile', 'default_print_profile','deretract_speed', 'disable_fan_first_layers',
                'dont_support_bridges', 'draft_shield','duplicate_distance', 'elefant_foot_compensation',
                'enable_dynamic_fan_speeds','enable_dynamic_overhang_speeds', 'end_filament_gcode', 'end_gcode',
                'external_perimeter_acceleration', 'external_perimeter_extrusion_width', 'external_perimeter_speed',
                'external_perimeters_first', 'extra_loading_move', 'extra_perimeters', 'extra_perimeters_on_overhangs',
                'extruder_clearance_height', 'extruder_clearance_radius', 'extruder_colour', 'extruder_offset',
                'extrusion_axis', 'extrusion_multiplier', 'extrusion_width', 'fan_always_on', 'fan_below_layer_time',
                'filament_colour', 'filament_cooling_final_speed', 'filament_cooling_initial_speed',
                'filament_cooling_moves', 'filament_cost', 'filament_density', 'filament_diameter', 'filament_load_time',
                'filament_loading_speed', 'filament_loading_speed_start', 'filament_max_volumetric_speed',
                'filament_minimal_purge_on_wipe_tower', 'filament_multitool_ramming', 'filament_multitool_ramming_flow',
                'filament_multitool_ramming_volume', 'filament_notes', 'filament_ramming_parameters',
                'filament_retract_before_travel', 'filament_retract_before_wipe', 'filament_retract_layer_change',
                'filament_retract_length', 'filament_retract_lift', 'filament_retract_speed', 'filament_settings_id',
                'filament_soluble', 'filament_spool_weight', 'filament_toolchange_delay', 'filament_type',
                'filament_unload_time', 'filament_unloading_speed', 'filament_unloading_speed_start', 'filament_vendor',
                'filament_wipe', 'fill_angle', 'fill_density', 'fill_pattern', 'first_layer_acceleration',
                'first_layer_acceleration_over_raft', 'first_layer_bed_temperature', 'first_layer_extrusion_width',
                'first_layer_height', 'first_layer_speed', 'first_layer_speed_over_raft', 'first_layer_temperature',
                'full_fan_speed_layer', 'fuzzy_skin', 'fuzzy_skin_point_dist', 'fuzzy_skin_thickness', 'gap_fill_enabled',
                'gap_fill_speed', 'gcode_comments', 'gcode_flavor', 'gcode_label_objects', 'gcode_resolution',
                'gcode_substitutions', 'high_current_on_filament_swap', 'host_type', 'infill_acceleration',
                'infill_anchor', 'infill_anchor_max', 'infill_every_layers', 'infill_extruder', 'infill_extrusion_width',
                'infill_first', 'infill_overlap', 'infill_speed', 'interface_shells', 'ironing', 'ironing_flowrate',
                'ironing_spacing', 'ironing_speed', 'ironing_type', 'layer_gcode', 'layer_height', 'machine_limits_usage',
                'machine_max_acceleration_e', 'machine_max_acceleration_extruding', 'machine_max_acceleration_retracting',
                'machine_max_acceleration_travel', 'machine_max_acceleration_x', 'machine_max_acceleration_y',
                'machine_max_acceleration_z', 'machine_max_feedrate_e', 'machine_max_feedrate_x', 'machine_max_feedrate_y',
                'machine_max_feedrate_z', 'machine_max_jerk_e', 'machine_max_jerk_x', 'machine_max_jerk_y',
                'machine_max_jerk_z', 'machine_min_extruding_rate', 'machine_min_travel_rate', 'max_fan_speed',
                'max_layer_height', 'max_print_height', 'max_print_speed', 'max_volumetric_extrusion_rate_slope_negative',
                'max_volumetric_extrusion_rate_slope_positive', 'max_volumetric_speed', 'min_bead_width', 'min_fan_speed',
                'min_feature_size', 'min_layer_height', 'min_print_speed', 'min_skirt_length',
                'mmu_segmented_region_interlocking_depth', 'mmu_segmented_region_max_width', 'notes', 'nozzle_diameter',
                'only_retract_when_crossing_perimeters', 'ooze_prevention', 'output_filename_format',
                'overhang_fan_speed_0', 'overhang_fan_speed_1', 'overhang_fan_speed_2', 'overhang_fan_speed_3',
                'overhang_speed_0', 'overhang_speed_1', 'overhang_speed_2', 'overhang_speed_3', 'overhangs',
                'parking_pos_retraction', 'pause_print_gcode', 'perimeter_acceleration', 'perimeter_extruder',
                'perimeter_extrusion_width', 'perimeter_generator', 'perimeter_speed', 'perimeters',
                'physical_printer_settings_id', 'post_process', 'print_settings_id', 'printer_model', 'printer_notes',
                'printer_settings_id', 'printer_technology', 'printer_variant', 'printer_vendor',
                'raft_contact_distance', 'raft_expansion', 'raft_first_layer_density', 'raft_first_layer_expansion',
                'raft_layers', 'remaining_times', 'resolution', 'retract_before_travel', 'retract_before_wipe',
                'retract_layer_change', 'retract_length', 'retract_length_toolchange', 'retract_lift',
                'retract_lift_above', 'retract_lift_below', 'retract_restart_extra', 'retract_restart_extra_toolchange',
                'retract_speed', 'seam_position', 'silent_mode', 'single_extruder_multi_material',
                'single_extruder_multi_material_priming', 'skirt_distance', 'skirt_height', 'skirts', 
                'slice_closing_radius', 'slicing_mode', 'slowdown_below_layer_time', 'small_perimeter_speed',
                'solid_infill_acceleration', 'solid_infill_below_area', 'solid_infill_every_layers',
                'solid_infill_extruder', 'solid_infill_extrusion_width', 'solid_infill_speed', 'spiral_vase',
                'staggered_inner_seams', 'standby_temperature_delta', 'start_filament_gcode', 'start_gcode',
                'support_material', 'support_material_angle', 'support_material_auto',
                'support_material_bottom_contact_distance', 'support_material_bottom_interface_layers',
                'support_material_buildplate_only', 'support_material_closing_radius', 'support_material_contact_distance',
                'support_material_enforce_layers', 'support_material_extruder', 'support_material_extrusion_width',
                'support_material_interface_contact_loops', 'support_material_interface_extruder',
                'support_material_interface_layers', 'support_material_interface_pattern', 'support_material_interface_spacing',
                'support_material_interface_speed', 'support_material_pattern', 'support_material_spacing',
                'support_material_speed', 'support_material_style', 'support_material_synchronize_layers',
                'support_material_threshold', 'support_material_with_sheath', 'support_material_xy_spacing',
                'support_tree_angle', 'support_tree_angle_slow', 'support_tree_branch_diameter',
                'support_tree_branch_diameter_angle', 'support_tree_branch_diameter_double_wall', 'support_tree_branch_distance',
                'support_tree_tip_diameter', 'support_tree_top_rate', 'temperature', 'template_custom_gcode', 'thick_bridges',
                'thin_walls', 'threads', 'thumbnails', 'thumbnails_format', 'toolchange_gcode', 'top_fill_pattern',
                'top_infill_extrusion_width', 'top_solid_infill_acceleration', 'top_solid_infill_speed', 'top_solid_layers',
                'top_solid_min_thickness', 'travel_acceleration', 'travel_speed', 'travel_speed_z', 'use_firmware_retraction',
                'use_relative_e_distances', 'use_volumetric_e', 'variable_layer_height', 'wall_distribution_count',
                'wall_transition_angle', 'wall_transition_filter_deviation', 'wall_transition_length', 'wipe', 'wipe_into_infill',
                'wipe_into_objects', 'wipe_tower', 'wipe_tower_bridging', 'wipe_tower_brim_width', 'wipe_tower_cone_angle',
                'wipe_tower_extra_spacing', 'wipe_tower_extruder', 'wipe_tower_no_sparse_layers', 'wipe_tower_rotation_angle',
                'wipe_tower_width', 'wipe_tower_x', 'wipe_tower_y', 'wiping_volumes_extruders', 'wiping_volumes_matrix',
                'xy_size_compensation', 'z_offset']
    options_set = []
    type = config_type.GCODE
    def __init__(self,config_string: 'str') -> None:
        if type(config_string) == bytes:
            config_string = config_string.decode('utf-8')
            self.type = self.config_type.GCODE
        else:
            self.type = self.config_type.INI
        def seek_substring(self,substring):
            self.id = self.string.find(substring)
            self.id += len(substring) if self.id != -1 else 0
        self.string = config_string
        self.id = 0
        for option in self.options_names:
            seek_substring(self,str('\n; ' + option + ' = ') if self.type == self.config_type.GCODE else str('\n' + option + ' = '))
            self.options_set.append(config_string[self.id:].split(';' if self.type == self.config_type.GCODE else '\n')[0] if self.id >= 0 else ' ')

    def __str__(self):
        return self.string

    def get_config_param(self,option: 'str'):
        return self.options_set[self.options_names.index(option)]


# Opens, verifies and parses a given stl-file
# ----------------------------------------
# Input: STL-File path (string)
# Output: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
def openSTL(path: 'str'):
    file_path = path
    # Creating exception classes to store correct info
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

        lines = 0               #counting the number of lines in the STL
        curr_triangle = 1
        for line in file:
            lines += 1

        num_triangles = int((lines-2)/7) #each triangle has info on 7 lines

        triangles = np.zeros([num_triangles,12],dtype=float) #initializing array 

        linenr = 1
        file.seek(0)
        if file.readline().rsplit(' ')[0] != ('solid'):  #STLs start with solid 'NAME'
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
                #isAscii = True
                bin_file.close()                #reopens File in ASCII read mode
                ascii_file = open(file_path,'r')    #reopens File in ASCII read mode
                triangles = checkParseAsciiSTL(ascii_file)
                ascii_file.close()
                print('ASCII file valid at:', file_path)
                return triangles
            else:
                print('Found Binary File at:', file_path)
                #isBinary = True
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
        finally:
            bin_file.close()
    else:
        print(file_path, 'is not an STL File')

# Writes a valid STL-File to pass to the slicer
# ----------------------------------------
# Input: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
# Output: path of the written STL-File
def writeSTL(triangles: 'np.ndarray[np.float]'):
    path = 'temp_slicing_'+time.strftime('%d%m%Y_%H%M%S', time.localtime())+'.stl'
    file = open(path,'xb')
    file.write(b' '.ljust(80))
    num_triangles = len(triangles[:,0])
    file.write(struct.pack('<i',num_triangles))
    for triangle in triangles:
        file.write(struct.pack('<12f',*triangle))
        file.write(b'  ')
    file.close()
    print('Written', num_triangles,'triangles')
    return path

# recognizes the outline of a flat stl-surface
# ----------------------------------------
# Input: Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the base of an STL or a whole STL 
# Output: Numpy array of shape [NUMBER_TRIANGLES,12 with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3] of the newly generated block STL that is flat and has height z_mean
def genBlock(stl_triangles: 'np.ndarray[np.float]', z_mean: 'np.float'):
    #z_min = np.min(stl_triangles[:,[5,8,11]])
    #stl_triangles[:,[5,8,11]] -= z_min
    testarr = ~np.bitwise_and.reduce((np.isclose(stl_triangles[:,5::3],np.zeros_like(stl_triangles[:,5::3]),1e-17)),axis=1) #detects lines where z is sufficiently close to 0
    base_triangles = np.delete(stl_triangles,testarr,axis=0) #gets rid of all lines where z is not within a specified tolerance to 0
    top_triangles = base_triangles.copy()
    top_triangles[:,2] *= -1
    base_triangles[:,[5,8,11]] = 0
    top_triangles[:,[5,8,11]] = z_mean

    triangles_check = np.concatenate((base_triangles[:,[3,4,6,7]],base_triangles[:,[6,7,9,10]],base_triangles[:,[3,4,9,10]]),axis=0)
    triangles_check = np.concatenate((triangles_check,triangles_check[:, [2, 3, 0, 1]]))

    uniq,idx,count= np.unique(triangles_check,return_index=True,return_counts=True,axis=0)
    count = count[idx.argsort()]
    uniq = uniq[idx.argsort()]
    uniq = uniq[np.logical_not((count-1).astype(bool))]
    uniq = uniq[:len(uniq)//2]
    sides = np.zeros((2*len(uniq[:,0]),12))
    sides[:,11] = z_mean
    sides[len(uniq[:,0]):,8] = z_mean
    sides[len(uniq[:,0]):,[3,4,6,7]] = uniq
    sides[len(uniq[:,0]):,[9,10]] = uniq[:,0:2]
    sides[:len(uniq[:,0]),[6,7,9,10]] = uniq
    sides[:len(uniq[:,0]),[3,4]] = uniq[:,2:]
    flat_stl = np.concatenate((base_triangles,top_triangles,sides),axis=0)
    flat_stl[:,0:3] = 0
    print('Generated Block STL Data with', len(flat_stl[:,0]), 'triangles')
    return flat_stl
    #return uniq, triangles_check

# Opens, verifies and parses a given GCODE-file
# ----------------------------------------
# Input: GCODE-File path (string), reading mode (mmap, manual, None) 
# Output: [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
def openGCODE(path: 'str'):
    with open(path,'r') as file: # checks length of file to estimate array size to allocate
        lines = 0
        for line in file:
            lines += 1
    gcode_arr = np.full(lines,np.nan,dtype=gcode_dtype) #initializes an array of NaN's with a custom datatype, i.o. to acces each value by name
    with open(path,'r') as f:  #opening file with context manager
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm: #initializes file memory mapping
            line_list = []
            line_nr = 0 
            while line_nr<lines:
                splitline = mm.readline().replace(b'\n',b'').split(b';')
                line_list = splitline[0].strip().split(b' ')
                comment = splitline[1:]
                if line_list[0] == b'G1':  #if the current line is a moving line
                    gcode_arr[line_nr]['Instruction'] = 'G1'
                    for single_inst in line_list[1:]: #for loop through the entries of every line
                        gcode_arr[line_nr][chr(single_inst[0])] = single_inst[1:] #puts it in the corresponding field
                else:
                    gcode_arr[line_nr]['Instruction'] = (b' '.join(line_list)).decode('utf-8')
                if(comment):
                    if(comment[0].startswith(b'TYPE')):
                        gcode_arr[line_nr]['Instruction'] = (b';' + comment[0]).decode('utf-8')
                if(comment):
                    if(comment[0].startswith(b'WIDTH')):
                        gcode_arr[line_nr]['Instruction'] = (b';' + comment[0]).decode('utf-8')
                
                if(comment):
                    if(comment[0].startswith(b'Z:')): 
                        gcode_arr[line_nr]['Instruction'] = (b';' + comment[0]).decode('utf-8')
                
                line_nr += 1 #counts actual amount of moving lines
    return gcode_arr


# Opens, verifies and parses a given GCODE-file while retaining all comments
# ----------------------------------------
# Input: GCODE-File path (string), get_config (if to return the string of the config at the end of the sliced gcode)
# Output: [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
def openGCODE_keepcoms(path: 'str', get_config = True):
    with open(path,'r') as file: # checks length of file to estimate array size to allocate
        lines = 0
        for line in file:
            if line.startswith('; prusaslicer_config = begin'):
                break
            lines += 1
    gcode_arr = np.full(lines,np.nan,dtype=gcode_dtype) #initializes an array of NaN's with a custom datatype, i.o. to acces each value by name
    with open(path,'r') as f:  #opening file with context manager
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm: #initializes file memory mapping
            line_list = []
            line_nr = 0 
            while line_nr<lines:
                splitline = mm.readline().replace(b'\n',b'').replace(b'\r',b'').split(b';')
                line_list = splitline[0].strip().split(b' ')
                comment = splitline[1:]
                if line_list[0] == b'G1':  #if the current line is a moving line
                    gcode_arr[line_nr]['Instruction'] = 'G1'
                    for single_inst in line_list[1:]: #for loop through the entries of every line
                        gcode_arr[line_nr][chr(single_inst[0])] = single_inst[1:] #puts it in the corresponding field
                elif(comment and (line_list != [b''])): 
                    gcode_arr[line_nr]['Instruction'] = (b' '.join(line_list + [b';'] + [comment[0].strip()])).decode('utf-8') 
                elif(comment and (line_list == [b''])): 
                    gcode_arr[line_nr]['Instruction'] = (b';'.join([b''] + comment)).decode('utf-8') 
                else:
                    gcode_arr[line_nr]['Instruction'] = (b' '.join(line_list)).decode('utf-8') 
                line_nr += 1 #counts actual amount of moving lines
            if(get_config == True):
                prusa_config = mm.read()
                prusa_config = slicer_config(prusa_config)
                return gcode_arr, prusa_config.__str__()
            else:
                return gcode_arr


def openINI(path: 'str'):
    with open(path,'r') as f:
        return f.read()

# Testing Code:
if __name__ == "__main__":     
    path_stl_ascii = 'Scheibe.stl' #Filename definition
    path_gcode = 'test_files/Scheibe.gcode' #filename definition
    path_stl_bin = 'Scheibe_bin.stl' #filename definition

    start = time.time()
    openSTL(path_stl_ascii)
    end = time.time()
    print('ASCII time:', end-start, 's')

#    start = time.time()
#    openSTL_lib(path_stl_ascii)
#    end = time.time()
#    print('ASCII library time:', end-start, 's')

    start = time.time()
    openSTL(path_stl_bin)
    end = time.time()
    print('Binary time:', end-start, 's')

#    start = time.time()
#    openSTL_lib(path_stl_bin)
#    end = time.time()
#    print('Binary library time:', end-start, 's')

    start = time.time()
    openGCODE(path_gcode,mode='mmap')
    end = time.time()
    print('Memory mapped time:', end-start, 's')


    start = time.time()
    openGCODE(path_gcode,mode='manual')
    end = time.time()
    print('Normal file handling time:', end-start, 's')

    stl_triangles = openSTL('test_pa_outline_fein_2.stl')
    start = time.time()
    flat_points = genBlock(stl_triangles,10)
    end = time.time()
    writeSTL(flat_points)
    print('Baseline handling time:', end-start, 's')
