import surface
import numpy as np
from dataclasses import dataclass


class PrintInfo():
    def __init__(self, config, FullBottomLayers, FullTopLayers):
        
        self.layerheight = float(config.get_config_param('layer_height'))
        self.fullbottomlayers = FullBottomLayers
        self.fulltoplayers = FullTopLayers
        self.fullbottomheight = FullBottomLayers * self.layerheight
        self.fulltopheight = FullTopLayers * self.layerheight
        self.numfulllayer = FullBottomLayers + FullTopLayers    


# Resample and calculate
#----------------------------------------------------------------------
# Input:        stl             = Numpy array of shape [NUMBER_TRIANGLES,12] with [_,:] = [x_normal,y_normal,z_normal,x1,y1,z1,x2,y2,z2,x3,y3,z3]
#               surface_array   = Mesh of the interpolated z Values
#               limits          = np.array with the values [xmin, xmax, ymin, ymax]
#               transform_info  = Class Object from Class PrintInfo()
# Output: 
def trans_stl(stl: 'np.ndarray[np.float]' , surface_array: 'np.ndarray[np.float]', limits: 'np.ndarray[np.float]', transform_info):
    
    NormHeight = np.amax(stl[:,[5,8,11]])
    Layerheight = transform_info.layerheight
    MaxLayerNum = NormHeight / Layerheight
    FullBottomLayers = transform_info.fullbottomlayers
    FullTopLayers = transform_info.fulltoplayers
    FullBottomHeight = transform_info.fullbottomheight
    FullTopHeight = transform_info.fulltopheight
    
    Output_array = np.zeros((stl.shape))
    for k in range(0,3):
        Output_array[:,3*k+3] = stl[:,3*k+3]
        Output_array[:,3*k+4] = stl[:,3*k+4]
        Z_Surface = surface_array[np.round((stl[:,3*k+4] - limits[2])).astype(int), np.round((stl[:,3*k+3] - limits[0])).astype(int)]
        Z_STL = stl[:,3*k+5]
        deltaZ = Z_Surface - Z_STL
        index_z_higher_fullbottom = Z_STL > FullBottomHeight
        index_deltaz_lower_fulltop = deltaZ <= FullTopHeight
        Output_array[np.bitwise_and(index_deltaz_lower_fulltop, index_z_higher_fullbottom), 3*k+5] = NormHeight * deltaZ[np.bitwise_and(index_deltaz_lower_fulltop, index_z_higher_fullbottom)]
        Output_array[np.bitwise_and(index_z_higher_fullbottom,np.bitwise_not(index_deltaz_lower_fulltop)), 3*k+5] = (1 - (deltaZ[np.bitwise_and(index_z_higher_fullbottom,np.bitwise_not(index_deltaz_lower_fulltop))] - FullTopHeight) / (Z_Surface[np.bitwise_and(index_z_higher_fullbottom,np.bitwise_not(index_deltaz_lower_fulltop))] - FullTopHeight)) * (NormHeight - FullTopHeight)
        Output_array[np.bitwise_not(index_z_higher_fullbottom), 3*k+5] = Z_STL[np.bitwise_not(index_z_higher_fullbottom)]
        # ------------this is the non parallelised structure!---------------
        # if Z_STL > FullBottomHeight:
        #     if deltaZ <= FullTopHeight:
        #         Output_array[:,3*k+5] = NormHeight - deltaZ
        #     else:
        #         Output_array[:,3*k+5] = (1 - (deltaZ - FullTopHeight) / (Z_Surface - FullTopHeight)) * (NormHeight - FullTopHeight)
        # else:
        #     Output_array[:, 3*k+5] = Z_STL
        index_negativ = np.where(Output_array[:,3*k+5] < 0)
        Output_array[index_negativ,3*k+5] = 0
       
    
    return Output_array


# Resample and calculate the transformed GCode according to the surface --> Curved Adaptive Layer Slicing (CLAS)
#----------------------------------------------------------------------
# Input: Gcode in Arrayform ->  [NUMBER_MOVE_INSTRUCTIONS,1] with [_,:] = [('Instruction','<U30'),('X','f8'),('Y','f8'),('Z','f8'),('E','f8'),('F','i')]
#        Computed Surface Array from surface.py -> .shape = [n,3] with its columns [x, y, z]
#        Printer, now between "DeltiQ2" or "MK3"
# Output: File in the explorer with the transformed Gcode


def trans_gcode(orig_gcode: 'np.ndarray[np.float]', surface_array: 'np.ndarray[np.float]', limits: 'np.ndarray[np.float]' = 0, printer="DeltiQ2",config_string:'str'=False):
    fullbottomlayer = 4
    fulltoplayer = 4
    layerheight = 0.2           # in mm
    resolution = 0.02           # in mm
    subg_resolution = 1         # in mm
    
    print("Calculating Surface Interpolation")
    gradx_mesh, grady_mesh, gradz = surface.create_gradient(surface_array, limits)
    xmesh, ymesh, zmesh = surface.create_surface_extended(surface_array, limits, resolution)
    #zmesh = surface.create_surface_array(surface_array, resolution, limits)
    
    file = open('nonplanar.gcode', 'w')
    
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
    
    if printer == "MK3":
        x_offset = 125
        y_offset = 105

    length = 0
    
    y_min = limits[2]
    x_min = limits[0]
    
    # Calculate the maximal layer number
    z_heights = orig_gcode["Instruction"][np.char.startswith(orig_gcode["Instruction"], ";Z:")]
    z_max = float(max(np.char.replace(z_heights, ";Z:", "")) ) 
    
    maxlayernum = np.round((z_max / layerheight),0).astype(int)
    
    numline = orig_gcode.shape[0]
    numfulllayer = fullbottomlayer + fulltoplayer
    numvariablelayer = maxlayernum - numfulllayer
    
    print("Transformation Progress running...")
    
    for i in range(0, numline):         # Loop over every Line in the original GCode
        
        #Overview how long it will take :)
        teiler = np.round((numline / 4),0)
        mod_i = i % teiler
        if mod_i == 0:
            procent = np.round(i / numline * 100, 0)
            
            print("Progress: ", procent, "%")
            
        if i == numline:
            print("Progress: 100.0%")
            
        # Take the current Z layer directly out of the slicer
        z_raw_instruction = orig_gcode["Instruction"][i]
        if np.char.startswith(z_raw_instruction, ";Z:"):
            z_curr = float(z_raw_instruction.replace(";Z:", ""))
        
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
                                actual_g_line[:,2] = interpol_z - ((maxlayernum - layernum) * layerheight)
                            
                            if layernum > fullbottomlayer:
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
    
    print("GCode Transformation finished. Enjoy")
    if config_string != False:
        file.write(config_string)
        
    file.close()
    return True