import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
import filereader as fr
import prusa_slicer as ps
import surface as sf
import numpy as np
import gcode_transform_1 as gc1
import os
import transform as tf
import platform
import matplotlib.pyplot as plt

demo_on = 0

# Setup Default Paths if nothing is marked
stl_default = "test_files/Welle_Phase.stl"
stl_default = "test_files/test_pa_ironing.stl"
config_default = "test_files/generic_config_Deltiq2_ironing_raft.ini"

# Create the window with its Context
dpg.create_context()

# get current Operating system -> "windows" = Windows, "darwin" = Mac OS
os_current = platform.system()
print(os_current)

if os_current == "Windows":
    prusaslicer_default_path = "C:\Program Files\Prusa3D\PrusaSlicer"
    
if os_current == "Darwin":
    prusaslicer_default_path = 'Use "Change Prusaslicer Path" for defining Path'

# Standard comment as path
stl_dir = "C:/ "
config_dir = "C:/ "

stl_path_dir_default = stl_dir
config_path_dir_default = config_dir

max_angle_default = 40


# Interupthandling if a button or similiar is activated
def stl_chosen(sender, app_data, user_data):
    stl_dir = app_data["file_path_name"]
    dpg.set_value("checkbox_cad", False)
    dpg.set_value("stl_text", stl_dir)
    
def config_chosen(sender, app_data, user_data):
    config_dir = app_data["file_path_name"]
    dpg.set_value("checkbox_config", False)
    dpg.set_value("config_text", config_dir)
    
def slicer_chosen(sender, app_data, user_data):
    prusaslicer_default_path = app_data["file_path_name"]
    dpg.set_value("slicer_text", prusaslicer_default_path)
    
def default_cad_path(sender, app_data, user_data):
    if app_data:
        stl_dir = stl_default
        dpg.set_value("stl_text", stl_dir)
    
def default_config_path(sender, app_data, user_data):
    if app_data:
        config_dir = config_default
        dpg.set_value("config_text", config_dir)
        
def case1_marked(sender, app_data, user_data):
    if app_data:
        dpg.set_value("checkbox_case2", False)
    else:
        dpg.set_value("checkbox_case1", True)
    
def case2_marked(sender, app_data, user_data):
    if app_data:
        dpg.set_value("checkbox_case1", False)
    else:
        dpg.set_value("checkbox_case2", True)
        
def show_preview_surface(sender, app_data, user_data):
    current_stl_path = dpg.get_value("stl_text") 
    if current_stl_path == stl_path_dir_default:
        stl_dir = stl_default
    else:
        stl_dir = current_stl_path
        
    orig_stl = fr.openSTL(stl_dir)
    filtered_surface = sf.create_surface(orig_stl,np.deg2rad(45))

    
def show_gcode_prusaslicer(sender, app_data, user_data):
    ps.viewGCODE("nonplanar.gcode", dpg.get_value("slicer_text"))
    
               
def calculate_button(sender, app_data, user_data):
    # if the paths are changed to a custom one
    if dpg.get_value("stl_text") == stl_path_dir_default :
        stl_dir = stl_default
        dpg.set_value("stl_text", stl_dir)
        dpg.set_value("checkbox_cad", True)
    
    if dpg.get_value("config_text") == config_path_dir_default:
        config_dir = config_default
        dpg.set_value("config_text", config_dir)
        dpg.set_value("checkbox_config", True)
    
    dpg.set_value("showtext_calculate_button", "calculation started")
        

    # Start with the calculation
    dpg.show_item("loading")
    
# ---------------------------------Function for slicing etc. here ---------------------------------------
    if os.path.exists(dpg.get_value("slicer_text")+"\prusa-slicer-console.exe"):
        if dpg.get_value("checkbox_case1"):
            # Here goes the calculations for Case 1
            # Open the .stl to the triangle Array
            triangle_array = fr.openSTL(dpg.get_value("stl_text"))
            # Get the Config as String to determine the layerheight etc.
            config = fr.slicer_config(fr.openINI(dpg.get_value("config_text")))
            # Define PrintInfo for Layerheight infos etc.
            printSetting = gc1.PrintInfo(config,FullBottomLayers=4, FullTopLayers=4, resolution_zmesh = 0.05)
            # Calculate the Surface Array
            filtered_surface, limits = sf.create_surface(triangle_array, np.deg2rad(dpg.get_value('max_angle_input'))) # Winkel
            print("Calculating Surface Interpolation")
            # Calculate the nearest extrapolated points outside of the surface
            xmesh, ymesh, zmesh = sf.create_surface_extended(filtered_surface, limits, printSetting.resolution)
            # Calculate the gradient of the surface for extruding optimizing
            gradx_mesh, grady_mesh, gradz = sf.create_gradient(filtered_surface, limits)
            # Transform the .stl for slicing
            transformed_stl = gc1.trans_stl(triangle_array, zmesh, limits, printSetting)
            # write the .stl to a temp file
            temp_stl_path = fr.writeSTL(transformed_stl)
            # repair damaged triangles in the .stl (wrong surface direction -> normalvector wrong)
            ps.repairSTL(temp_stl_path)
            # Slice the transformed .stl
            ps.sliceSTL(temp_stl_path,dpg.get_value("config_text"),'--info', dpg.get_value("slicer_text"))
            # Load the sliced and generated .gcode in an array
            orig_gcode, config = fr.openGCODE_keepcoms("output.gcode", get_config=True)
            # Transform the gcode according to the Surface
            gc1.trans_gcode(orig_gcode, gradz, zmesh,  printSetting, limits, config_string=config)
            # Delete the temp generated .stl
            #os.remove(temp_stl_path)
        
        if dpg.get_value("checkbox_case2"):
            # Here goes the calculations for Case 2
            orig_stl = fr.openSTL(dpg.get_value("stl_text"))
            filtered_surface, limits = sf.create_surface(orig_stl,np.deg2rad(dpg.get_value('max_angle_input')))
            transformed_stl = tf.projectSTL(orig_stl,filtered_surface,method='mirror')
            temp_stl_path = fr.writeSTL(transformed_stl)
            ps.sliceSTL(temp_stl_path,config_dir,'--info')
            ps.repairSTL(temp_stl_path)
            os.remove(temp_stl_path)
            planar_gcode = fr.openGCODE('output.gcode')

        # finishing informations for the User
        dpg.hide_item("loading")
        dpg.set_value("showtext_calculate_button", "Finished Gcode ready, Enjoy")
        
    else:
        dpg.hide_item("loading")
        dpg.set_value("showtext_calculate_button", "Prusaslicer Executable couldn't be found in given directory!")
    

# Here are the File dialog defined
with dpg.file_dialog(directory_selector=False, show=False, callback=stl_chosen, id="stl_select", width=700 ,height=400):
    dpg.add_file_extension(".stl", color=(255, 255, 255, 255))
    
with dpg.file_dialog(directory_selector=True, show=False, callback=slicer_chosen, id="slicer_select", width=700 ,height=400):
    dpg.add_file_extension("")
    
with dpg.file_dialog(directory_selector=False, show=False, callback=config_chosen, id="slicer_config", width=700 ,height=400):
    dpg.add_file_extension(".ini", color=(255, 255, 255, 255))

# Custom Window with the corresponding buttons etc.
with dpg.window(label="GCode Transformation", width=1000, height=500):
    
    with dpg.group(horizontal=True):
        dpg.add_text("------------------------------------ Select Path -----------------------------------------------")
    # Select the CAD File
    with dpg.group(horizontal=True):
        dpg.add_text("default:", tag="text_default_cad")
        dpg.add_checkbox(label="    ", callback=default_cad_path, tag="checkbox_cad")
        
        dpg.add_button(label="Select CAD File", callback=lambda: dpg.show_item("stl_select"), width=200)
        dpg.add_text("  Directory: ")
        dpg.add_text(stl_dir, tag="stl_text")
        
    # Select the Config File
    with dpg.group(horizontal=True):
        dpg.add_text("default:", tag="text_default_config")
        dpg.add_checkbox(label="    ", callback=default_config_path,  tag="checkbox_config")
        
        dpg.add_button(label="Select Prusaslicer Config", callback=lambda: dpg.show_item("slicer_config"), width=200)
        dpg.add_text("  Directory: ")
        dpg.add_text(config_dir, tag="config_text")
        
    with dpg.group(horizontal=True):
        dpg.add_button(label="Change Prusaslicer DIR", callback=lambda: dpg.show_item("slicer_select"), width=200)
        dpg.add_text(" Current Directory: ")
        dpg.add_text(prusaslicer_default_path, tag="slicer_text")
    
    with dpg.group(horizontal=True):
        dpg.add_text("")
        
    with dpg.group(horizontal=True):
        dpg.add_text("------------------------------------ Slicing options -----------------------------------------------")
    
    # Select the Case with checkboxes
    with dpg.group(horizontal=True):
        dpg.add_text("Select a Case:     ")
        dpg.add_text("Case 1 ", tag="text_case1")
        
        dpg.add_checkbox(label="     ", tag="checkbox_case1", callback=case1_marked, default_value=True)
        dpg.add_text("Case 2", tag="text_case2")
        dpg.add_checkbox(tag="checkbox_case2", callback=case2_marked)
        
    with dpg.group(horizontal=True):
        dpg.add_text("Select the maximal printing angle:", tag ='text_max_angle')
        dpg.add_input_int(tag = 'max_angle_input', default_value=max_angle_default, width=100)
        
    with dpg.group(horizontal=True):
        dpg.add_text("------------------------------------ Start Calculation -----------------------------------------")
    
    # Select the Calculate Button
    with dpg.group(horizontal=True):   
        dpg.add_button(label="Calculate GCode", callback=calculate_button)
        dpg.add_button(label="Show Surface preview", callback=show_preview_surface)
        dpg.add_button(label="Open Nonplanar GCode", callback=show_gcode_prusaslicer)
        
    with dpg.group(horizontal=True):        
        dpg.add_loading_indicator(tag="loading", show=False, radius=1.5)
        dpg.add_text("", tag="showtext_calculate_button")
               
        
#Tooltips: (hovering over Items to show additional Information)
    # Case 1 Infos
    with dpg.tooltip("text_case1"):
            dpg.add_text("tbd: Hier kommt die Beschreibung von Fall 1 hinein")
    
    # Case 2 Infos      
    with dpg.tooltip("text_case2"):
            dpg.add_text("tbd: Hier kommt die Beschreibung von Fall 2 hinein")
       
    # Default Path for CAD Infos     
    with dpg.tooltip("text_default_cad"):
        dpg.add_text("The default Path is:")
        dpg.add_text(stl_default)
    
    # Default Path for Config file Infos    
    with dpg.tooltip("text_default_config"):
        dpg.add_text("The default Path is:")
        dpg.add_text(config_default)
        
    with dpg.tooltip('text_max_angle'):
        dpg.add_text("Angle between the horizontal plane and the surface")
        
# Create the Window with custom Commands
dpg.create_viewport(title='Nonplanar Slicing', width=1000, height=500)

#--------------------------------
# Delete late this rows...
# show the demo -> What is possible
if demo_on == 1:
    demo.show_demo()
#--------------------------------   
    
# Create the window and show it to the user
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
