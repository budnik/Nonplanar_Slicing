import numpy as np
from dataclasses import dataclass


class PrintInfo():
    def __init__(self, config, FullBottomLayers, FullTopLayers, resolution_zmesh = 0.02):
        
        self.layerheight = float(config.get_config_param('layer_height'))
        self.fullbottomlayers = FullBottomLayers
        self.fulltoplayers = FullTopLayers
        self.fullbottomheight = FullBottomLayers * self.layerheight
        self.fulltopheight = FullTopLayers * self.layerheight
        self.numfulllayer = FullBottomLayers + FullTopLayers    
        self.resolution = resolution_zmesh
        self.ironing = bool(config.get_config_param('ironing'))
        self.path = ''


# Resample and calculate
#----------------------------------------------------------------------
# Input:        stl             = Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
#               surface_array   = Mesh of the interpolated z Values
#               limits          = np.array with the values [xmin, xmax, ymin, ymax]
#               transform_info  = Class Object from Class PrintInfo()
# Output:       Transformed stl with a planar surface, except the nondetected surface points
def trans_stl(stl: 'np.ndarray[np.float]' , surface_array: 'np.ndarray[np.float]', limits: 'np.ndarray[np.float]', transform_info):
    
    NormHeight = np.mean(surface_array)
    print(NormHeight)
    Layerheight = transform_info.layerheight
    FullBottomHeight = transform_info.fullbottomheight
    FullTopHeight = transform_info.fulltopheight
    resolution = transform_info.resolution
    
    Output_array = np.zeros((stl.shape))
    # Copy the normalvector to the output array
    Output_array[:, :3] = stl[:, :3]
    for k in range(0,3):
        # copy the x values of the given stl
        Output_array[:,3*k+3] = stl[:,3*k+3]
        # copy the y values into the output stl
        Output_array[:,3*k+4] = stl[:,3*k+4]
        
        Z_Surface = surface_array[np.round((stl[:,3*k+4] - limits[2])*(1/resolution)).astype(int), np.round((stl[:,3*k+3] - limits[0])*(1/resolution)).astype(int)]
        Z_STL = stl[:,3*k+5]
        deltaZ = Z_Surface - Z_STL
        index_z_higher_fullbottom = Z_STL > FullBottomHeight
        index_deltaz_lower_fulltop = deltaZ <= FullTopHeight
        
        if1 = np.logical_and(index_deltaz_lower_fulltop, index_z_higher_fullbottom)
        if2 = np.logical_and(index_z_higher_fullbottom,np.logical_not(index_deltaz_lower_fulltop))
        if3 = np.logical_not(index_z_higher_fullbottom)
        
        Output_array[if1, 3*k+5] = NormHeight - deltaZ[if1]
        Output_array[if2, 3*k+5] = (1 - (deltaZ[if2] - FullTopHeight) / (Z_Surface[if2] - FullTopHeight)) * (NormHeight - FullTopHeight)
        Output_array[if3, 3*k+5] = Z_STL[if3]      
        
        index_negativ = Output_array[:,3*k+5] < 0
        Output_array[index_negativ,3*k+5] = 0
        index_to_high = Output_array[:,3*k+5] > NormHeight
        Output_array[index_to_high,3*k+5] = NormHeight
       
    
    return Output_array


# Resample and calculate the transformed GCode according to the surface
#----------------------------------------------------------------------
# Input: orig_gcode = Gcode in Arrayform ->  [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
#        gradz = Computed gradient Array for every coordinate of the mesh
#        zmesh = Computed Surface Array from surface.py -> .shape = [n,3] with its columns [x, y, z]
#        file_info = Printinfo Class with information related to the print -> fulltopheight, interpolation resolution etc.
#        limits = max and min values of the stl part
#        printer = Change Offset of buildplate -> now between "DeltiQ2" or "MK3"
#        config_string = The whole configpart at the end of the GCode
#        
# Output: File in the explorer with the transformed Gcode


def trans_gcode(orig_gcode: 'np.ndarray[np.float]', gradz: 'np.ndarray[np.float]', zmesh: 'np.ndarray[np.float]', file_info, limits: 'np.ndarray[np.float]' = 0, printer="DeltiQ2",config_string:'str'=False):
    
    fullbottomlayer = file_info.fullbottomlayers
    fulltoplayer = file_info.fulltoplayers
    layerheight = file_info.layerheight            # in mm
    resolution = file_info.resolution              # in mm
    subg_resolution = 1                            # in mm
    
    file = open(file_info.path, 'w')
    
    x = 0
    y = 0
    z = 0
    
    z_old = 0
    
    G1_str = "G1"
    x_str = " X"
    y_str = " Y"
    z_str = " Z"
    e_str = " E"
    f_str = " F"
    
    format_move = 'G1 X%.3f Y%.3f Z%.4f'
    format = 'G1 X%.3f Y%.3f Z%.4f E%.4f'
    
    x_offset = 0
    y_offset = 0
    # creates an Offset depending of the printer
    if printer == "MK3":
        x_offset = 125
        y_offset = 105

    length = 0
    z_ironing = 0
    corr_ironing = 0.05
    
    y_min = limits[2]
    x_min = limits[0]
    
    # Calculate the maximal layer number
    z_heights = orig_gcode["Instruction"][np.char.startswith(orig_gcode["Instruction"], ";Z:")]
    z_max = float(max(np.char.replace(z_heights, ";Z:", "")) ) 
    # calculate the final layer numbers
    maxlayernum = np.round((z_max / layerheight),0).astype(int)
    
    numline = orig_gcode.shape[0]
    numfulllayer = fullbottomlayer + fulltoplayer
    numvariablelayer = maxlayernum - numfulllayer
    
    print("Transformation Progress running...")
    
    for i in range(0, numline):         # Loop over every Line in the original GCode
        
        #Overview how long it will take :)
        divider = np.round((numline / 4),0)
        mod_i = i % divider
        if mod_i == 0:
            percent = np.round(i / numline * 100, 0)
            
            print("Progress: ", percent, "%")
            
        if i == numline:
            print("Progress: 100.0%")
            
        # Take the current Z layer directly out of the slicer
        z_raw_instruction = orig_gcode["Instruction"][i]
        if np.char.startswith(z_raw_instruction, ";Z:"):
            z_curr = float(z_raw_instruction.replace(";Z:", ""))
            
        if z_raw_instruction == ";TYPE:Ironing":
            z_ironing = -0.02            
        
        if orig_gcode["Instruction"][i] == "G1":
            
            if np.isnan(x) == False:
                x_old = x
            if np.isnan(y) == False:
                y_old = y
            
            # Read the current Line and reset the value to the old if it is NaN
            x = orig_gcode["X"][i]               
            y = orig_gcode["Y"][i]
            e = orig_gcode["E"][i]
            f = orig_gcode["F"][i]
            z = orig_gcode["Z"][i]
            
            if np.isnan(z) == False:
                z_offset = z - z_curr
            
            # Main calculation if its a valid linear movement of the print itself
                
            #calculate layerheight
            layernum = np.round((z_curr/layerheight),0)
                
            if layernum > fullbottomlayer:  # skip the calculation of the bottom Layer if false
                                        
                    # everytime it is a move command in X and Y direction, do it
                    if (np.isnan(x) == False) and (np.isnan(y) == False):
                        
                        length = np.round((np.sqrt((x-x_old)**2 + (y-y_old)**2 + 1)),0)
                                           
                        # we work here with the standard 1mm resolution für the sub Gcode
                        j = np.linspace(1, length, (length/subg_resolution).astype(int))
                        
                        # calculate all x and y values between the start and end point of the G1 Line
                        x_new = np.round(x_old + (x-x_old)/length * j, 3)
                        y_new = np.round(y_old + (y-y_old)/length * j, 3)
                        
                        actual_g_line = np.zeros((x_new.shape[0], 4))
                        actual_g_line[:, 0] = x_new[:]
                        actual_g_line[:, 1] = y_new[:]
                        
                        interpol_z = zmesh[np.round((actual_g_line[:,1] - y_min - y_offset)*(1/resolution)).astype(int), np.round((actual_g_line[:,0] - x_min - x_offset)*(1/resolution)).astype(int)]

                        if (np.isnan(e) == False): # if its a normal print line
                            
                            
                            # current planar layer is in the middle (variable layer) 
                            if layernum > fullbottomlayer and layernum <= (maxlayernum - fulltoplayer):
                                actual_g_line[:,2] = (layernum - fullbottomlayer) * (interpol_z - numfulllayer * layerheight) / (numvariablelayer) + fullbottomlayer * layerheight
                                #correction for layerheight difference
                                scaling_factor = ((interpol_z - numfulllayer * layerheight) / (numvariablelayer * layerheight))
                                actual_g_line[:,3] = (e/length) * scaling_factor
                                
                            else:
                                actual_g_line[:,3] = e / length 
                                
                            #current planar layer is in the top full layer
                            if layernum > (maxlayernum - fulltoplayer):
                                actual_g_line[:,2] = interpol_z - ((maxlayernum - layernum) * layerheight) + z_ironing * corr_ironing * (interpol_z - maxlayernum * layerheight)
                            
                            if layernum > fullbottomlayer:
                                # if ironing == True:
                                #     corr_factor = 1
                                # else:
                                #     corr_factor =  (1-(gradz[np.round((y_new[0]-y_min-y_offset)*2, 0).astype(int)-1, np.round((x_new[0]-x_min-x_offset)*2, 0).astype(int)-1]**1.5))
                                corr_factor =  (1-(gradz[np.round((y_new[0]-y_min-y_offset)*2, 0).astype(int)-1, np.round((x_new[0]-x_min-x_offset)*2, 0).astype(int)-1]**1.5))
                                actual_g_line[:,3] = actual_g_line[:,3] * corr_factor
                                                            
                            
                            #create an Offset if current z is not the actual z
                            actual_g_line[:,2] += z_offset
                            
                            #save last z Value for moving commands without printing (with offset)
                            z_old = actual_g_line[-1, 2]
                                                     
                            np.savetxt(file, actual_g_line, fmt = format)  
                            
                        if np.isnan(e): # if its a moving line (without print -> e = NaN)
                            # current planar layer is in the middle (variable layer) 
                            if layernum > fullbottomlayer and layernum <= (maxlayernum - fulltoplayer):
                                actual_g_line[:,2] = (layernum - fullbottomlayer) * (interpol_z - numfulllayer * layerheight) / (numvariablelayer) + fullbottomlayer * layerheight
                                
                            #current planar layer is in the top full layer
                            if layernum > (maxlayernum - fulltoplayer):
                                actual_g_line[:,2] = interpol_z - ((maxlayernum - layernum) * layerheight)
                            
                            #create an Offset if current z is not the actual z
                            actual_g_line[:,2] += z_offset
                            
                            #save last z Value for moving commands without printing (with offset)
                            z_old = actual_g_line[-1, 2]
                            
                            np.savetxt(file, actual_g_line[:,:3], fmt = format_move)                   
                        
                    else: # if the current line is not a normal move line but a E or Z or F line
                        
                        # if only z move G1 Line -> it wants to make an offset to move above the part
                        if np.isnan(x) and np.isnan(y) and (np.isnan(z) == False) and np.isnan(e):
                            z = np.round((z_old + z_offset), 3)
                        
                        add_str = G1_str
                        if (np.isnan(x) == False) or (np.isnan(y) == False):
                            print("Exceptionbehandlung Hier!")  # wird nur bei Bewegung in eine Richtung getriggert
                        if (np.isnan(z) == False):
                            add_str = add_str + z_str +str(z)
                        if (np.isnan(e) == False):
                            add_str = add_str + e_str +str(e)
                        if (np.isnan(f) == False):
                            add_str = add_str + f_str +str(f)
                            
                        file.write(add_str  + '\n')
                        
    
            else: # the G1 stays because it is the bottom layer, so just add the Line
                
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
    
    print("GCode Transformation finished")
    if config_string != False:
        file.write(config_string)
    
    # Close File and finish method 1
    file.close()
    return True