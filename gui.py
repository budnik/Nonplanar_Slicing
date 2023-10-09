import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

demo_on = 0

dpg.create_context()
stl_dir = "C:\ "
config_dir = "C:\ "

def stl_chosen(sender, app_data, user_data):
    stl_dir = app_data["file_path_name"]
    dpg.set_value("stl_text", stl_dir)
    
def config_chosen(sender, app_data, user_data):
    config_dir = app_data["file_path_name"]
    print(app_data)
    dpg.set_value("config_text", config_dir)
    
def calculate_button(sender, app_data, user_data):
    print(len(dpg.get_value("stl_text")))
    if (len(dpg.get_value("stl_text")) > 4) and( len(dpg.get_value("config_text")) > 4):
        dpg.set_value("showtext_calculate_button", "calculation started")
        #Hier Modulaufruf einsetzen!!
        
        
    else:
        dpg.set_value("showtext_calculate_button", "Warning, please define a path for the .stl and .ini config!")
        

with dpg.file_dialog(directory_selector=False, show=False, callback=stl_chosen, id="stl_select", width=700 ,height=400):
    dpg.add_file_extension(".stl", color=(255, 255, 255, 255))

with dpg.file_dialog(directory_selector=False, show=False, callback=config_chosen, id="slicer_config", width=700 ,height=400):
    dpg.add_file_extension(".ini", color=(255, 255, 255, 255))


with dpg.window(label="Slicer Settings", width=1000, height=300):
    
    with dpg.group(horizontal=True):
        dpg.add_button(label="Select CAD File", callback=lambda: dpg.show_item("stl_select"), width=200)
        dpg.add_text("  Directory: ")
        dpg.add_text(stl_dir, tag="stl_text")
    
    with dpg.group(horizontal=True):
        dpg.add_button(label="Select Prusaslicer Config", callback=lambda: dpg.show_item("slicer_config"), width=200)
        dpg.add_text("  Directory: ")
        dpg.add_text(config_dir, tag="config_text")
    
    with dpg.group(horizontal=True):   
        dpg.add_button(label="Calculate GCode", callback=calculate_button )
        dpg.add_text("", tag="showtext_calculate_button")




dpg.create_viewport(title='Nonplanar Slicing', width=800, height=600)

if demo_on == 1:
    demo.show_demo()
    
    
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
