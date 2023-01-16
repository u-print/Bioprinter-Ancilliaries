# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 13:54:51 2022

@author: ollpo511
"""

input("Welcome to the U-PRINT bioprinter well to plate script. Press any key to start.")

import re

def insert_gcode(gcode):
    modified_gcode = []
    T_pattern = re.compile("^T")
    for i, line in enumerate(gcode):
        if T_pattern.match(line) and "layer" not in gcode[i-1]:
            modified_gcode.append(line)
            modified_gcode.append("G1 R2 X0 Y0 F10000\n")
            modified_gcode.append("G1 R2 Z0 F5000\n")
        else:
            modified_gcode.append(line)
    return modified_gcode


try:
    import numpy as np
    import cv2 as cv
    import matplotlib.pyplot as plt
except:
    raise ImportError("Pre-requisite packages numpy and OpenCV not found. Please install these packages.")
    input()
#import ipdb

START_LINE = 209
END_LINE = 790
preambleChange=False


#Read in: G-Code, Array, Distance

def readGCode(fn):
    objGCode = []
    try:
        with open(fn + ".gcode") as fh:
            for line in fh:
                objGCode.append(line)
    except:
        print("Could not load")
        return
    return objGCode

#Safecheck that it doesnt impact walls?

#Concatenate

def concatObjects(ObjectGCode, plateGeometry, displacement, startingPoint = [0,0], wellChangeMacro_fn = ''):
    wellChangeMacro = None
    totalGCode = []
    if(wellChangeMacro_fn != ''):
        #Extra gcode between objects
        wellChangeMacro=readGCode(wellChangeMacro_fn)
    #Total amount of wells is given by rows (pGeo[0]) and cols (pGeo[1])
    for cols in range(startingPoint[0],plateGeometry[0]):
        for rows in range(startingPoint[1],plateGeometry[1]):
            totalGCode.extend(translateGCode(ObjectGCode, [rows*displacement, cols*displacement]))
            if(wellChangeMacro!=None):
                totalGCode.extend(wellChangeMacro)
    totalGCode = insert_gcode(totalGCode)
    return totalGCode

#Translate G-code

def translateGCode(construct, displacement):
    preambleChange = False
    firstTC = False
    #Assume construct is an array of strings
    modifiedGCode = []
    #Capture positions into group1 and group2
    G1XYString = "(G\d) X(\d{1,4}.\d{1,4}) Y(\d{1,4}.\d{1,4})"
    G1XYPattern = re.compile(G1XYString)
    #Capture layer changes
    ZString = "(G\d) Z(\d{1,4}.\d{1,4})"
    ZPattern = re.compile(ZString)
    en = enumerate(construct)


    for index,line in en:
        zMove = re.search(ZPattern, line)
        modLine = line
        #Ignore commented lines
        if(line[0] != ";"):
            if(re.search("^T\d",line) and firstTC == False):
                next(en)
                print("TC")
                firstTC=True
            originalPos = re.search(G1XYPattern, line)
            #Find z movement that is not the actual last line of the file
            if(bool(zMove) and line != construct[-1] and preambleChange == False):              
                #Is the z move followed by an XY move?
                print("Zmove")
                layerChange = re.search(G1XYPattern, construct[index+1])
                if(bool(layerChange)): 
                    print(f"Exchanging: {line} with {construct[index+1]}")
                    originalX = float(layerChange[2])
                    originalY = float(layerChange[3])
                    transX = round(originalX+displacement[0],3)
                    transY = round(originalY+displacement[1],3)
                    replacementString = f"{layerChange[1]} X{transX} Y{transY}"
                    modifiedGCode.append(re.sub(G1XYPattern,replacementString, construct[index+1]))
                    next(en)
                    preambleChange = True
            #Capture the original positions we want
            elif(bool(originalPos)):
                originalX = float(originalPos[2])
                originalY = float(originalPos[3])
                transX = round(originalX+displacement[0],3)
                transY = round(originalY+displacement[1],3)
                replacementString = f"{originalPos[1]} X{transX} Y{transY}"
                modLine = re.sub(G1XYPattern,replacementString, line)
        modifiedGCode.append(modLine)
    return modifiedGCode

def createArrayNames(startWell,rows,cols):
    startrow = startWell[0]
    startcol = startWell[1]
    wells = np.empty(shape=(cols,rows),dtype=object)
    wells[0,0] = startWell
    for row in range(rows):
        for col in range(cols):
            well = str(chr(ord(startrow)+row))+str(int(startcol)+int(col))
            wells[col,row] = well
    return wells
    

def outputConcat(totalGCode, fn):
    with open(fn+".gcode",mode='w') as fh:
        for line in totalGCode:
            fh.write(f"{line}")
            
if __name__ == '__main__':   
    # startingwell="B2"
    # displacement = 25
    # obj_fn="220906_halfsphere"
    # rows=4
    # cols=4
    # transitionalMacroFn=''
    #startingwell = input("What well do you want to place the first object in? Format as A1 or D3 e.g. \n")  
    startingwell = "A1"
    displacement = -int(input("What is the distance between the center of each well?\n"))
    obj_fn = input(f"Filename of single object positioned in {startingwell}?\n")    
    rows = int(input("How many rows should be printed?\n"))
    cols = int(input("How many columns should be printed?\n"))
    transitionalMacroFn= input("Filename of gcode to run between objects? Leave empty if none.\n")
    names = createArrayNames(startingwell,cols,rows)
    basex = 75
    basey = 75
    rows = names.shape[0]
    cols = names.shape[1]
    maxx = max([rows * (-displacement*5)+basex,600])
    maxy = max([cols * (-displacement*5)+basey,600])
    img = np.zeros(shape=(maxx,maxy),dtype=np.uint8)
    
    
    for col in range(cols):
        for row in range(rows):
            cposx = basex-displacement*col*5
            cposy = basey-displacement*row*5
            img = cv.circle(img,(cposx,cposy),40,(255,255,255),-1)
            img = cv.putText(img,names[row,col],org = (cposx-20,cposy+15), fontFace=cv.FONT_HERSHEY_SIMPLEX,fontScale=1,color = (0,255,0),thickness=2,lineType=cv.LINE_AA)
    
    fig = plt.figure()
    plt.imshow(img)
    plt.savefig(f"{obj_fn}_r{rows}_c{cols}.png")
    obj = readGCode(obj_fn)
    orig_obj = obj
    total = concatObjects(obj, [cols,rows], displacement,[0,0], transitionalMacroFn)
    outputConcat(total,f"{obj_fn}_r{rows}_c{cols}.gcode")
    input("Showing image. Press any key to exit.")
    