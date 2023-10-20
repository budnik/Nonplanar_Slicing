import surface
import numpy as np


# Resample and calculate the transformed GCode according to the surface
#----------------------------------------------------------------------
# Input: Gcode in Arrayform and surface from surface module
#        Computed Surface Array from surface.py
# Output: List of Strings with new Gcode instruction

def trans_gcode(orig_gcode, surface_array):
    fullbottomlayer = 4
    fulltoplayer = 4
    maxlayernum = 25
    layerheight = 0.2
    resolution = 0.05
    
    gradx_mesh, grady_mesh, gradz = surface.create_gradient(surface_array)
    
    zmesh = surface.create_surface_array(surface_array, resolution)

    section_arr = np.zeros((0, 4))      # Array for calculating the G1 Line sectionwise -> [x, y, z, e]
    
    file = open('nonplanar.gcode', 'w')
    
    x = 0
    y = 0
    z = 0
    
    G1_str = "G1"
    x_str = " X"
    y_str = " Y"
    z_str = " Z"
    e_str = " E"
    f_str = " F"
    
    x_offset = 125
    y_offset = 105
    
    still_G1_line = False
    line_offset = 0
    length = 0
    
    y_min = np.min(surface_array[:,1])
    x_min = np.min(surface_array[:,0])
    
    numline = orig_gcode.shape[0]
    numfulllayer = fullbottomlayer + fulltoplayer
    numvariablelayer = maxlayernum - numfulllayer
    
    for i in range(0, numline):         # Loop over every Line in the original GCode
        
        #Overview how long it will take :)
        still_G1_line = False
        mod_i = i % 500
        if mod_i == 0:
            print("Prozent: ", i, "/", numline)
            
        if i == 4255:
            donothing = False
            doonce = False
        
        
        # General Code
        if orig_gcode["Instruction"][i] == "G1":
            
            if np.isnan(x) == False:
                x_old = x
            if np.isnan(y) == False:
                y_old = y
            if np.isnan(z) == False:
                z_old = z
            
            # Read the current Line and reset the value to the old if it is NaN
            x = orig_gcode["X"][i]               
            y = orig_gcode["Y"][i]
            e = orig_gcode["E"][i]
            f = orig_gcode["F"][i]
            z = orig_gcode["Z"][i]
            if np.isnan(z):
                z = z_old
            
            # Main calculation if its a valid linear movement of the print itself
            valid_line = (np.isnan(x) == False) and (np.isnan(x) == False) and (np.isnan(e) == False)
            if valid_line:
                
                #calculate layerheight
                layernum = np.round((z/layerheight),0)
                
                if layernum > fullbottomlayer:  # skip the calculation of the bottom Layer if false
                    # set true to indicate we are still in 
                    still_G1_line = True
                    
                    length = np.round((np.sqrt((x-x_old)**2 + (y-y_old)**2 + 1)),1)
                    
                    #print(length, "Linie: ", i)
                    # we work here with the standard 1mm resolution für the sub Gcode
                    j = np.linspace(1, length, np.round(length, 0).astype(int))
                    
                    # calculate all x and y values between the start and end point of the G1 Line
                    x_new = np.round(x_old + (x-x_old)/length * j, 3)
                    y_new = np.round(y_old + (y-y_old)/length * j, 3)
                    #z_new = z_old + (z-z_old)/length * j
                    
                    temp_actual_g_line = np.zeros((x_new.shape[0], 4))
                    temp_actual_g_line[:, 0] = x_new[:]
                    temp_actual_g_line[:, 1] = y_new[:]
                    section_arr = np.concatenate((section_arr, temp_actual_g_line), axis=0)
                    
                     
                     
                    
                else: # the G1 stays because it is the bottom layer, so just add the Line
                    #new_array += [f"{G1_str}{x_str}{x}{y_str}{y}{e_str}{e}"]
                    file.write(f"G1 X{orig_gcode['X'][i]} Y{orig_gcode['Y'][i]} E{orig_gcode['E'][i]}\n")
                    
                    
                    
            else:     # If this "else" is called, it is a G1 Line, but not one with X, Y and E movement and gets directly stored
                              
                add_str = G1_str
                if (np.isnan(x) == False):
                    add_str = add_str + x_str +str(x)
                if (np.isnan(y) == False):
                    add_str = add_str + y_str +str(y)
                if (np.isnan(z) == False):
                    add_str = add_str + z_str +str(z)
                if (np.isnan(e) == False):
                    add_str = add_str + e_str +str(e)
                if (np.isnan(f) == False):
                    add_str = add_str + f_str +str(f)
                                
                file.write(add_str  + '\n')


        else:       # If the "else" is called, the line should be copied as it is at the current line
            file.write(orig_gcode["Instruction"][i] + '\n') 
            #new_array.append(orig_gcode["Instruction"][i])
        
        if (still_G1_line == False) and (length != 0) and valid_line:
            
            # interpolate the temp saved x and y values
            xy_new_coord = np.concatenate([[section_arr[:,0]-x_offset], [section_arr[:,1]-y_offset]]).T
            #interpol_z = np.ones((xy_new_coord.shape[0],))
            #interpol_z = surface.interpolate_grid(xy_new_coord, surface_array)
            interpol_z = zmesh[np.round((section_arr[:,1] - y_min - y_offset)*(1/resolution)).astype(int), np.round((section_arr[:,0] - x_min - x_offset)*(1/resolution)).astype(int)]
            #np.savetxt("interpol_z.txt", interpol_z)
            # current planar layer is in the midle (variable layer) 
            if layernum > fullbottomlayer and layernum <= (maxlayernum - fulltoplayer):
                section_arr[:,2] = (layernum - fullbottomlayer) * (interpol_z - numfulllayer * layerheight) / (numvariablelayer) + fullbottomlayer * layerheight
                section_arr[:,3] = e/length * ((interpol_z - numfulllayer * layerheight) / (numvariablelayer * layerheight))
            else:
                section_arr[:,3] = e / length
                
            #current planar layer is in the top full layer
            if layernum > (maxlayernum - fulltoplayer):
                section_arr[:,2] = interpol_z - ((maxlayernum - layernum) * layerheight)
            
            if layernum > fullbottomlayer:
                
                section_arr[:,3] = section_arr[:,3] * (1-(gradz[np.round((y_new[0]-y_min-y_offset)*2, 0).astype(int)-1, np.round((x_new[0]-x_min-x_offset)*2, 0).astype(int)-1]**1.5))
            format = 'G1 X%.3f Y%.3f Z%.4f E%.4f'
            np.savetxt(file, section_arr, fmt = format)
            #clear out the written array
            section_arr = np.zeros((0, 4)) 
            
            
            # compute the new G1 String
            #new_array += [f"{G1_str}{x_str}{valuex}{y_str}{valuey}{z_str}{valuez}{e_str}{valuee}" for valuex, valuey, valuez, valuee in zip(x_new, y_new, ztrans, etrans)]
            
    print("Fertig :)")
        
# todo:
