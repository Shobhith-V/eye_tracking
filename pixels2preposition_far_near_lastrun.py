#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2024.2.1),
    on January 31, 2025, at 17:16
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
prefs.hardware['audioLib'] = 'ptb'
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER, priority)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard

# This section of the EyeLink Initialize component code imports some
# modules we need, manages data filenames, allows for dummy mode configuration
# (for testing experiments without an eye tracker), connects to the tracker,
# and defines some helper functions (which can be called later)
import pylink
import time
import platform
from PIL import Image  # for preparing the Host backdrop image
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from string import ascii_letters, digits
from psychopy import gui

import psychopy_eyelink
print('EyeLink Plugin For PsychoPy Version = ' + str(psychopy_eyelink.__version__))

script_path = os.path.dirname(sys.argv[0])
if len(script_path) != 0:
    os.chdir(script_path)

# Set this variable to True if you use the built-in retina screen as your
# primary display device on macOS. If have an external monitor, set this
# variable True if you choose to "Optimize for Built-in Retina Display"
# in the Displays preference settings.
use_retina = False

# Set this variable to True to run the script in "Dummy Mode"
dummy_mode = False

# Prompt user to specify an EDF data filename
# before we open a fullscreen window
dlg_title = "Enter EDF Filename"
dlg_prompt = "Please enter a file name with 8 or fewer characters [letters, numbers, and underscore]."
# loop until we get a valid filename
while True:
    dlg = gui.Dlg(dlg_title)
    dlg.addText(dlg_prompt)
    dlg.addField("Filename", "EDF Filename:","Test")
    # show dialog and wait for OK or Cancel
    ok_data = dlg.show()
    if dlg.OK:  # if ok_data is not None
        print("EDF data filename: {}".format(ok_data["Filename"]))
    else:
        print("user cancelled")
        core.quit()
        sys.exit()

    # get the string entered by the experimenter
    tmp_str = ok_data["Filename"]
    # strip trailing characters, ignore the ".edf" extension
    edf_fname = tmp_str.rstrip().split(".")[0]

    # check if the filename is valid (length <= 8 & no special char)
    allowed_char = ascii_letters + digits + "_"
    if not all([c in allowed_char for c in edf_fname]):
        print("ERROR: Invalid EDF filename")
    elif len(edf_fname) > 8:
        print("ERROR: EDF filename should not exceed 8 characters")
    else:
        break# Set up a folder to store the EDF data files and the associated resources
# e.g., files defining the interest areas used in each trial
results_folder = "results"
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# We download EDF data file from the EyeLink Host PC to the local hard
# drive at the end of each testing session, here we rename the EDF to
# include session start date/time
time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
session_identifier = edf_fname + time_str

# create a folder for the current testing session in the "results" folder
session_folder = os.path.join(results_folder, session_identifier)
if not os.path.exists(session_folder):
    os.makedirs(session_folder)

# For macOS users check if they have a retina screen
if 'Darwin' in platform.system():
    dlg = gui.Dlg("Retina Screen?")
    dlg.addText("What type of screen will the experiment run on?")
    dlg.addField("Screen Type", choices=["High Resolution (Retina, 2k, 4k, 5k)", "Standard Resolution (HD or lower)"])
    # show dialog and wait for OK or Cancel
    ok_data = dlg.show()
    if dlg.OK:
        if dlg.data["Screen Type"] == "High Resolution (Retina, 2k, 4k, 5k)":  
            use_retina = True
        else:
            use_retina = False
    else:
        print('user cancelled')
        core.quit()
        sys.exit()

# Connect to the EyeLink Host PC
# The Host IP address, by default, is "100.1.1.1".
# the "el_tracker" objected created here can be accessed through the Pylink
# Set the Host PC address to "None" (without quotes) to run the script
# in "Dummy Mode"
if dummy_mode:
    el_tracker = pylink.EyeLink(None)
else:
    try:
        el_tracker = pylink.EyeLink("100.1.1.1")
    except RuntimeError as error:
        dlg = gui.Dlg("Dummy Mode?")
        dlg.addText("Could not connect to tracker at 100.1.1.1 -- continue in Dummy Mode?")
        # show dialog and wait for OK or Cancel
        ok_data = dlg.show()
        if dlg.OK:  # if ok_data is not None
            dummy_mode = True
            el_tracker = pylink.EyeLink(None)
        else:
            print("user cancelled")
            core.quit()
            sys.exit()

eyelinkThisFrameCallOnFlipScheduled = False
eyelinkLastFlipTime = 0.0
zeroTimeIAS = 0.0
zeroTimeDLF = 0.0
sentIASFileMessage = False
sentDrawListMessage = False

def clear_screen(win,genv):
    """ clear up the PsychoPy window"""
    win.fillColor = genv.getBackgroundColor()
    win.flip()

def show_msg(win, genv, text, wait_for_keypress=True):
    """ Show task instructions on screen"""
    scn_width, scn_height = win.size
    msg = visual.TextStim(win, text,
                          color=genv.getForegroundColor(),
                          wrapWidth=scn_width/2)
    clear_screen(win,genv)
    msg.draw()
    win.flip()

    # wait indefinitely, terminates upon any key press
    if wait_for_keypress:
        kb = keyboard.Keyboard()
        waitKeys = kb.waitKeys(keyList=None, waitRelease=True, clear=True)
        clear_screen(win,genv)

def terminate_task(win,genv,edf_file,session_folder,session_identifier):
    """ Terminate the task gracefully and retrieve the EDF data file
    """
    el_tracker = pylink.getEYELINK()

    if el_tracker.isConnected():
        # Terminate the current trial first if the task terminated prematurely
        error = el_tracker.isRecording()
        if error == pylink.TRIAL_OK:
            abort_trial(win,genv)

        # Put tracker in Offline mode
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        pylink.msecDelay(500)

        # Close the edf data file on the Host
        el_tracker.closeDataFile()

        # Show a file transfer message on the screen
        msg = 'EDF data is transferring from EyeLink Host PC...'
        show_msg(win, genv, msg, wait_for_keypress=False)

        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        local_edf = os.path.join(session_folder, session_identifier + '.EDF')
        try:
            el_tracker.receiveDataFile(edf_file, local_edf)
        except RuntimeError as error:
            print('ERROR:', error)

        # Close the link to the tracker.
        el_tracker.close()

    # close the PsychoPy window
    win.close()

    # quit PsychoPy
    core.quit()
    sys.exit()

def abort_trial(win,genv):
    """Ends recording """
    el_tracker = pylink.getEYELINK()

    # Stop recording
    if el_tracker.isRecording():
        # add 100 ms to catch final trial events
        pylink.pumpDelay(100)
        el_tracker.stopRecording()

    # clear the screen
    clear_screen(win,genv)
    # Send a message to clear the Data Viewer screen
    bgcolor_RGB = (116, 116, 116)
    el_tracker.sendMessage('!V CLEAR %d %d %d' % bgcolor_RGB)

    # send a message to mark trial end
    el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)
    return pylink.TRIAL_ERROR

# this method converts PsychoPy position values to EyeLink position values
# EyeLink position values are in pixel units and are such that 0,0 corresponds 
# to the top-left corner of the screen and increase as position moves right/down
def eyelink_pos(pos,winSize):
    screenUnitType = 'pix'
    scn_width,scn_height = winSize
    if screenUnitType == 'pix':
        elPos = [pos[0] + scn_width/2,scn_height/2 - pos[1]]
    elif screenUnitType == 'height':
        elPos = [scn_width/2 + pos[0] * scn_height,scn_height/2 + pos[1] * scn_height]
    elif screenUnitType == "norm":
        elPos = [(scn_width/2 * pos[0]) + scn_width/2,scn_height/2 + pos[1] * scn_height]
    else:
        print("ERROR:  Only pixel, height, and norm units supported for conversion to EyeLink position units")
    return [int(round(elPos[0])),int(round(elPos[1]))]

# this method converts PsychoPy size values to EyeLink size values
# EyeLink size values are in pixels
def eyelink_size(size,winSize):
    screenUnitType = 'pix'
    scn_width,scn_height = winSize
    if len(size) == 1:
        size = [size[0],size[0]]
    if screenUnitType == 'pix':
        elSize = [size[0],size[1]]
    elif screenUnitType == 'height':
        elSize = [int(round(scn_height*size[0])),int(round(scn_height*size[1]))]
    elif screenUnitType == "norm":
        elSize = [size[0]/2 * scn_width,size[1]/2 * scn_height]
    else:
        print("ERROR:  Only pixel, height, and norm units supported for conversion to EyeLink position units")
    return [int(round(elSize[0])),int(round(elSize[1]))]

# this method converts PsychoPy color values to EyeLink color values
def eyelink_color(color):
    elColor = (int(round((win.color[0]+1)/2*255)),int(round((win.color[1]+1)/2*255)),int(round((win.color[2]+1)/2*255)))
    return elColor


# This method, created by the EyeLink MarkEvents component code, will get called to handle
# sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
# sending DV Target Position Messages, and/or logging DV video frame marking info=information
def eyelink_onFlip_MarkEvents(globalClock,win,scn_width,scn_height,allStimComponentsForEyeLinkMonitoring,\
    componentsForEyeLinkStimEventMessages,\
    componentsForEyeLinkStimDVDrawingMessages,dlf,dlf_file,\
    componentsForEyeLinkInterestAreaMessages,ias,ias_file,interestAreaMargins):
    global eyelinkThisFrameCallOnFlipScheduled,eyelinkLastFlipTime,zeroTimeDLF,sentDrawListMessage,zeroTimeIAS,sentIASFileMessage
    # this variable becomes true whenever a component offsets, so we can 
    # send Data Viewer messgaes to clear the screen and redraw still-present 
    # components.  set it to false until a screen clear is needed
    needToUpdateDVDrawingFromScreenClear = False
    # store a list of all components that need Data Viewer drawing messages 
    # sent for this screen retrace
    componentsForDVDrawingList = []
    # store a list of all components that need Data Viewer interest area messages 
    # sent for this screen retrace
    componentsForIAInstanceMessagesList = []
    # Log the time of the current frame onset for upcoming messaging/event logging
    currentFrameTime = float(globalClock.getTime())

    # Go through all stimulus components that need to be checked (for event marking,
    # DV drawing, and/or interest area logging) to see if any have just ONSET
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Check if the component has just onset
        if thisComponent.tStartRefresh is not None and not thisComponent.elOnsetDetected:
            # Check whether we need to mark stimulus onset (and log a trial variable logging this time) for the component
            if thisComponent in componentsForEyeLinkStimEventMessages:
                el_tracker.sendMessage('%s %s_ONSET' % (int(round((globalClock.getTime()-thisComponent.tStartRefresh)*1000)),thisComponent.name))
                el_tracker.sendMessage('!V TRIAL_VAR %s_ONSET_TIME %i' % (thisComponent.name,thisComponent.tStartRefresh*1000))
                # Convert the component's position to EyeLink units and log this value under .elPos
                # Also create lastelPos/lastelSize to store pos/size of the previous position, which is needed for IAS file writing
                thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                thisComponent.lastelPos = thisComponent.elPos
                thisComponent.lastelSize = thisComponent.elSize
            # If this is the first interest area instance of the trial write a message pointing
            # Data Viewer to the IAS file.  The time of the message will serve as the zero time point
            # for interest area information (e.g., instance start/end times) that is logged to the file
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                if not sentIASFileMessage:
                    # send an IAREA FILE command to let Data Viewer know where
                    # to find the IAS file to load interest area information
                    zeroTimeIAS = float(currentFrameTime)
                    el_tracker.sendMessage('%s !V IAREA FILE aoi/%s' % (int(round((globalClock.getTime()-currentFrameTime)*1000)),ias))
                    sentIASFileMessage = True
                thisComponent.iaInstanceStartTime = currentFrameTime
            if not sentDrawListMessage:
                # send an IAREA FILE command message to let Data Viewer know where
                # to find the IAS file to load interest area information
                zeroTimeDLF = float(currentFrameTime)
                # send a DRAW_LIST command message to let Data Viewer know where
                # to find the drawing messages to correctly present the stimuli
                el_tracker.sendMessage('%s !V DRAW_LIST graphics/%s' % (int(round((globalClock.getTime()-currentFrameTime)*1000))-3,dlf))
                dlf_file.write('0 CLEAR %d %d %d\n' % eyelink_color(win.color))
                sentDrawListMessage = True

            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                componentsForDVDrawingList.append(thisComponent)

            thisComponent.elOnsetDetected = True

    # Check whether any components that are being monitored for EyeLink purposes have changed position
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Get the updated position in EyeLink Units
        thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
        if thisComponent.elPos[0] != thisComponent.lastelPos[0] or thisComponent.elPos[1] != thisComponent.lastelPos[1]\
            and thisComponent.elOnsetDetected:
            # Only get an updated size if position has changed
            thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
            # log that we need to update the screen drawing with a clear command
            # and a redrawing of all still-present components
            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                needToUpdateDVDrawingFromScreenClear = True

            # log that we need to send an interest area instance message to the EDF
            # to mark the presentation that just ended
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                thisComponent.iaInstancePos = thisComponent.lastelPos
                thisComponent.iaInstanceSize = thisComponent.lastelSize
                componentsForIAInstanceMessagesList.append(thisComponent)

            # update the position (in EyeLink coordinates) for upcoming usage
            thisComponent.lastelPos = thisComponent.elPos
            thisComponent.lastelSize = thisComponent.elSize
    # Go through all stimulus components that need to be checked (for event marking,
    # DV drawing, and/or interest area logging) to see if any have just OFFSET
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Check if the component has just offset
        if thisComponent.tStopRefresh is not None and thisComponent.tStartRefresh is not None and \
            not thisComponent.elOffsetDetected:
            # send a message marking that component's offset in the EDF
            if thisComponent in componentsForEyeLinkStimEventMessages:
                el_tracker.sendMessage('%s %s_OFFSET' % (int(round((globalClock.getTime()-thisComponent.tStopRefresh)*1000)),thisComponent.name))
            # log that we need to update the screen drawing with a clear command
            # and a redrawing of all still-present components
            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                needToUpdateDVDrawingFromScreenClear = True
            # log that we need to send an interest area instance message to the EDF
            # to mark the presentation that just ended
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                thisComponent.iaInstancePos = thisComponent.lastelPos
                thisComponent.iaInstanceSize = thisComponent.lastelSize
                componentsForIAInstanceMessagesList.append(thisComponent)
            thisComponent.elOffsetDetected = True 
    # send an interest area message to the IAS file
    # see the section of the Data Viewer User Manual 
    # Protocol for EyeLink Data to Viewer Integrations -> Interest Area Commands
    for thisComponent in componentsForIAInstanceMessagesList:
        ias_file.write('%i %i IAREA %s %i %i %i %i %i %s\n' % \
            (int(round((zeroTimeIAS - thisComponent.iaInstanceStartTime)*1000)),
            int(round((zeroTimeIAS - currentFrameTime)*1000 + 1)),"RECTANGLE",thisComponent.iaIndex,
            thisComponent.iaInstancePos[0]-(thisComponent.iaInstanceSize[0]/2+interestAreaMargins),
            thisComponent.iaInstancePos[1]-(thisComponent.iaInstanceSize[1]/2+interestAreaMargins),
            thisComponent.iaInstancePos[0]+(thisComponent.iaInstanceSize[0]/2+interestAreaMargins),
            thisComponent.iaInstancePos[1]+(thisComponent.iaInstanceSize[1]/2+interestAreaMargins),thisComponent.name))
        thisComponent.iaInstanceStartTime = currentFrameTime
    # Send drawing messages to the draw list file so that the stimuli/placeholders can be viewed in 
    # Data Viewer's Trial View window
    # See the Data Viewer User Manual, sections:
    # Protocol for EyeLink Data to Viewer Integration -> Image Commands/Simple Drawing Commands
    # If any component has offsetted on this frame then send a clear message
    # followed by logging to send draw commands for all still-present components
    if needToUpdateDVDrawingFromScreenClear:
        dlf_file.write('%i CLEAR ' % (int(round((zeroTimeDLF - currentFrameTime)*1000)))
            + '%d %d %d\n' % eyelink_color(win.color))

        for thisComponent in componentsForEyeLinkStimDVDrawingMessages:
            if thisComponent.elOnsetDetected and not thisComponent.elOffsetDetected and thisComponent not in componentsForDVDrawingList:
                componentsForDVDrawingList.append(thisComponent)

    for thisComponent in componentsForDVDrawingList:
        # If it is an image component then send an image loading message
        if thisComponent.componentType == "Image":
            dlf_file.write('%i IMGLOAD CENTER ../../%s %i %i %i %i\n' % 
                (int(round((zeroTimeDLF - currentFrameTime)*1000)),
               thisComponent.image,thisComponent.elPos[0],
                thisComponent.elPos[1],thisComponent.elSize[0],thisComponent.elSize[1]))
        # If it is a sound component then skip the stimulus drawing message
        elif thisComponent.componentType == "sound" or thisComponent.componentType == "MovieStim3" or thisComponent.componentType == "MovieStimWithFrameNum":
            pass
        # If it is any other non-movie visual stimulus component then send
        # a draw command to provide a placeholder box in Data Viewer's Trial View window
        else:
            dlf_file.write('%i DRAWBOX 255 0 0 %i %i %i %i\n' % 
                (int(round((zeroTimeDLF - currentFrameTime)*1000)),
                thisComponent.elPos[0]-thisComponent.elSize[0]/2,
                thisComponent.elPos[1]-thisComponent.elSize[1]/2,
                thisComponent.elPos[0]+thisComponent.elSize[0]/2,
                thisComponent.elPos[1]+thisComponent.elSize[1]/2))
    # This logs whether a call to this method has already been scheduled for the upcoming retrace
    # And is used to help ensure we schedule only one callOnFlip call for each retrace
    eyelinkThisFrameCallOnFlipScheduled = False
    # This stores the time of the last retrace and can be used in Code components to 
    # check the time of the previous screen flip
    eyelinkLastFlipTime = float(currentFrameTime)
# This method, created by the EyeLink MarkEvents_2 component code, will get called to handle
# sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
# sending DV Target Position Messages, and/or logging DV video frame marking info=information
def eyelink_onFlip_MarkEvents_2(globalClock,win,scn_width,scn_height,allStimComponentsForEyeLinkMonitoring,\
    componentsForEyeLinkStimEventMessages,\
    componentsForEyeLinkStimDVDrawingMessages,dlf,dlf_file,\
    componentsForEyeLinkInterestAreaMessages,ias,ias_file,interestAreaMargins,\
    componentsForEyeLinkMovieFrameMarking):
    global eyelinkThisFrameCallOnFlipScheduled,eyelinkLastFlipTime,zeroTimeDLF,sentDrawListMessage,zeroTimeIAS,sentIASFileMessage
    # this variable becomes true whenever a component offsets, so we can 
    # send Data Viewer messgaes to clear the screen and redraw still-present 
    # components.  set it to false until a screen clear is needed
    needToUpdateDVDrawingFromScreenClear = False
    # store a list of all components that need Data Viewer drawing messages 
    # sent for this screen retrace
    componentsForDVDrawingList = []
    # store a list of all components that need Data Viewer interest area messages 
    # sent for this screen retrace
    componentsForIAInstanceMessagesList = []
    # Log the time of the current frame onset for upcoming messaging/event logging
    currentFrameTime = float(globalClock.getTime())

    # Go through all stimulus components that need to be checked (for event marking,
    # DV drawing, and/or interest area logging) to see if any have just ONSET
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Check if the component has just onset
        if thisComponent.tStartRefresh is not None and not thisComponent.elOnsetDetected:
            # Check whether we need to mark stimulus onset (and log a trial variable logging this time) for the component
            if thisComponent in componentsForEyeLinkStimEventMessages:
                el_tracker.sendMessage('%s %s_ONSET' % (int(round((globalClock.getTime()-thisComponent.tStartRefresh)*1000)),thisComponent.name))
                el_tracker.sendMessage('!V TRIAL_VAR %s_ONSET_TIME %i' % (thisComponent.name,thisComponent.tStartRefresh*1000))
                # Convert the component's position to EyeLink units and log this value under .elPos
                # Also create lastelPos/lastelSize to store pos/size of the previous position, which is needed for IAS file writing
                thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                thisComponent.lastelPos = thisComponent.elPos
                thisComponent.lastelSize = thisComponent.elSize
            # If this is the first interest area instance of the trial write a message pointing
            # Data Viewer to the IAS file.  The time of the message will serve as the zero time point
            # for interest area information (e.g., instance start/end times) that is logged to the file
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                if not sentIASFileMessage:
                    # send an IAREA FILE command to let Data Viewer know where
                    # to find the IAS file to load interest area information
                    zeroTimeIAS = float(currentFrameTime)
                    el_tracker.sendMessage('%s !V IAREA FILE aoi/%s' % (int(round((globalClock.getTime()-currentFrameTime)*1000)),ias))
                    sentIASFileMessage = True
                thisComponent.iaInstanceStartTime = currentFrameTime
            if not sentDrawListMessage:
                # send an IAREA FILE command message to let Data Viewer know where
                # to find the IAS file to load interest area information
                zeroTimeDLF = float(currentFrameTime)
                # send a DRAW_LIST command message to let Data Viewer know where
                # to find the drawing messages to correctly present the stimuli
                el_tracker.sendMessage('%s !V DRAW_LIST graphics/%s' % (int(round((globalClock.getTime()-currentFrameTime)*1000))-3,dlf))
                dlf_file.write('0 CLEAR %d %d %d\n' % eyelink_color(win.color))
                sentDrawListMessage = True

            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                componentsForDVDrawingList.append(thisComponent)

            thisComponent.elOnsetDetected = True

    # Check whether any components that are being monitored for EyeLink purposes have changed position
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Get the updated position in EyeLink Units
        thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
        if thisComponent.elPos[0] != thisComponent.lastelPos[0] or thisComponent.elPos[1] != thisComponent.lastelPos[1]\
            and thisComponent.elOnsetDetected:
            # Only get an updated size if position has changed
            thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
            # log that we need to update the screen drawing with a clear command
            # and a redrawing of all still-present components
            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                needToUpdateDVDrawingFromScreenClear = True

            # log that we need to send an interest area instance message to the EDF
            # to mark the presentation that just ended
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                thisComponent.iaInstancePos = thisComponent.lastelPos
                thisComponent.iaInstanceSize = thisComponent.lastelSize
                componentsForIAInstanceMessagesList.append(thisComponent)

            # update the position (in EyeLink coordinates) for upcoming usage
            thisComponent.lastelPos = thisComponent.elPos
            thisComponent.lastelSize = thisComponent.elSize
    # Go through all stimulus components that need to be checked (for event marking,
    # DV drawing, and/or interest area logging) to see if any have just OFFSET
    for thisComponent in allStimComponentsForEyeLinkMonitoring:
        # Check if the component has just offset
        if thisComponent.tStopRefresh is not None and thisComponent.tStartRefresh is not None and \
            not thisComponent.elOffsetDetected:
            # send a message marking that component's offset in the EDF
            if thisComponent in componentsForEyeLinkStimEventMessages:
                el_tracker.sendMessage('%s %s_OFFSET' % (int(round((globalClock.getTime()-thisComponent.tStopRefresh)*1000)),thisComponent.name))
            # log that we need to update the screen drawing with a clear command
            # and a redrawing of all still-present components
            if thisComponent in componentsForEyeLinkStimDVDrawingMessages:
                needToUpdateDVDrawingFromScreenClear = True
            # log that we need to send an interest area instance message to the EDF
            # to mark the presentation that just ended
            if thisComponent in componentsForEyeLinkInterestAreaMessages:
                thisComponent.iaInstancePos = thisComponent.lastelPos
                thisComponent.iaInstanceSize = thisComponent.lastelSize
                componentsForIAInstanceMessagesList.append(thisComponent)
            thisComponent.elOffsetDetected = True 
    # send an interest area message to the IAS file
    # see the section of the Data Viewer User Manual 
    # Protocol for EyeLink Data to Viewer Integrations -> Interest Area Commands
    for thisComponent in componentsForIAInstanceMessagesList:
        ias_file.write('%i %i IAREA %s %i %i %i %i %i %s\n' % \
            (int(round((zeroTimeIAS - thisComponent.iaInstanceStartTime)*1000)),
            int(round((zeroTimeIAS - currentFrameTime)*1000 + 1)),"RECTANGLE",thisComponent.iaIndex,
            thisComponent.iaInstancePos[0]-(thisComponent.iaInstanceSize[0]/2+interestAreaMargins),
            thisComponent.iaInstancePos[1]-(thisComponent.iaInstanceSize[1]/2+interestAreaMargins),
            thisComponent.iaInstancePos[0]+(thisComponent.iaInstanceSize[0]/2+interestAreaMargins),
            thisComponent.iaInstancePos[1]+(thisComponent.iaInstanceSize[1]/2+interestAreaMargins),thisComponent.name))
        thisComponent.iaInstanceStartTime = currentFrameTime
    # Send drawing messages to the draw list file so that the stimuli/placeholders can be viewed in 
    # Data Viewer's Trial View window
    # See the Data Viewer User Manual, sections:
    # Protocol for EyeLink Data to Viewer Integration -> Image Commands/Simple Drawing Commands
    # If any component has offsetted on this frame then send a clear message
    # followed by logging to send draw commands for all still-present components
    if needToUpdateDVDrawingFromScreenClear:
        dlf_file.write('%i CLEAR ' % (int(round((zeroTimeDLF - currentFrameTime)*1000)))
            + '%d %d %d\n' % eyelink_color(win.color))

        for thisComponent in componentsForEyeLinkStimDVDrawingMessages:
            if thisComponent.elOnsetDetected and not thisComponent.elOffsetDetected and thisComponent not in componentsForDVDrawingList:
                componentsForDVDrawingList.append(thisComponent)

    for thisComponent in componentsForDVDrawingList:
        # If it is an image component then send an image loading message
        if thisComponent.componentType == "Image":
            dlf_file.write('%i IMGLOAD CENTER ../../%s %i %i %i %i\n' % 
                (int(round((zeroTimeDLF - currentFrameTime)*1000)),
               thisComponent.image,thisComponent.elPos[0],
                thisComponent.elPos[1],thisComponent.elSize[0],thisComponent.elSize[1]))
        # If it is a sound component then skip the stimulus drawing message
        elif thisComponent.componentType == "sound" or thisComponent.componentType == "MovieStim3" or thisComponent.componentType == "MovieStimWithFrameNum":
            pass
        # If it is any other non-movie visual stimulus component then send
        # a draw command to provide a placeholder box in Data Viewer's Trial View window
        else:
            dlf_file.write('%i DRAWBOX 255 0 0 %i %i %i %i\n' % 
                (int(round((zeroTimeDLF - currentFrameTime)*1000)),
                thisComponent.elPos[0]-thisComponent.elSize[0]/2,
                thisComponent.elPos[1]-thisComponent.elSize[1]/2,
                thisComponent.elPos[0]+thisComponent.elSize[0]/2,
                thisComponent.elPos[1]+thisComponent.elSize[1]/2))

    # Send movie frame event messages and video frame draw messages for Data Viewer
    # integration.  # See the Data Viewer User Manual, section
    # Protocol for EyeLink Data to Viewer Integration -> Video Commands
    for thisComponent in componentsForEyeLinkMovieFrameMarking:
        sendFrameMessage = 0
        #Check whether the movie playback has begun yet
        if thisComponent.tStartRefresh is not None:
            # Check the movie class type to identify the frame identifier
            # MovieStim3 does not provide the frame index, so we need to determine
            # it manually based on the value of the current frame time
            if thisComponent.componentType == "MovieStim3":
                # MovieStim3 does not report the frame number or index, but does provide the 
                # frame onset time for the current frame. We can use this to identify each
                # frame increase
                vidFrameTime = thisComponent.getCurrentFrameTime()
                # Wait until the video has begun and define frame_index
                if not thisComponent.firstFramePresented:
                    # reset frame_index to 0
                    thisComponent.elMarkingFrameIndex = 0
                    # log that we will have sent the video onset marking message
                    # for future iterations/frames
                    thisComponent.firstFramePresented = True
                    # log that we need to send a message marking the current frame onset
                    sendFrameMessage = 1
                # check whether we have started playback and are on a new frame and if 
                # so then update our variables
                if thisComponent.elMarkingFrameIndex >= 0 and vidFrameTime > thisComponent.previousFrameTime:
                    thisComponent.elMarkingFrameIndex = thisComponent.elMarkingFrameIndex + 1
                    sendFrameMessage = 1
                    thisComponent.previousFrameTime = vidFrameTime
            # else if we are using a movie stim class that provides the current
            # frame number then we can grab the frame number directly
            else:
                # Other movie players have access to the frame number
                frameNum = thisComponent.getCurrentFrameNumber()
                vidFrameTime = currentFrameTime
                # If we have a new frame then update the frame number and log
                # that we need to send a frame-marking message
                if frameNum >= 0 and frameNum is not thisComponent.elMarkingFrameIndex:
                    thisComponent.elMarkingFrameIndex = frameNum
                    sendFrameMessage = 1
            # If we need to mark a frame onset, then with the above frame_index and 
            # currentTime variables defined, update the times, frame level messages and 
            # interest are information
            if sendFrameMessage == 1:
                # send a message to mark the onset of each frame
                el_tracker.sendMessage('%s %s_Frame %d' % (int(round((globalClock.getTime()-vidFrameTime)*1000)),thisComponent.name,thisComponent.elMarkingFrameIndex))
                # Write a VFRAME message to mark the onset of each frame
                # Format: VFRAME frame_num pos_x, pos_y, path_to_file
                # See the Data Viewer User Manual, section:
                # Protocol for EyeLink Data to Viewer Integration -> Video Commands
                if thisComponent.componentType == "MovieStim3":
                    vidFrameTime = currentFrameTime
                    dlf_file.write('%i VFRAME %d %d %d ../../%s\n' % (int(round((zeroTimeDLF - vidFrameTime)*1000+3)),
                        thisComponent.elMarkingFrameIndex,
                      int(round(thisComponent.elPos[0]-thisComponent.elSize[0]/2.0)),
                      int(round(thisComponent.elPos[1]-thisComponent.elSize[1]/2.0)),
                      thisComponent.filename))
                else:
                    dlf_file.write('%i VFRAME %d %d %d ../../%s\n' % (int(round((zeroTimeDLF - vidFrameTime)*1000+3)),
                        thisComponent.elMarkingFrameIndex,
                      int(round(thisComponent.elPos[0]-thisComponent.elSize[0]/2.0)),
                      int(round(thisComponent.elPos[1]-thisComponent.elSize[1]/2.0)),
                      thisComponent.filename))
                # Log that we don't need to send a new frame message again
                # until a new frame is actually drawn/detected
                sendFrameMessage = 0
    # This logs whether a call to this method has already been scheduled for the upcoming retrace
    # And is used to help ensure we schedule only one callOnFlip call for each retrace
    eyelinkThisFrameCallOnFlipScheduled = False
    # This stores the time of the last retrace and can be used in Code components to 
    # check the time of the previous screen flip
    eyelinkLastFlipTime = float(currentFrameTime)
# --- Setup global variables (available in all functions) ---
# create a device manager to handle hardware (keyboards, mice, mirophones, speakers, etc.)
deviceManager = hardware.DeviceManager()
# ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
# store info about the experiment session
psychopyVersion = '2024.2.1'
expName = 'PunjabiActivePassive'  # from the Builder filename that created this script
# information about this experiment
expInfo = {
    'ID': '',
    'participant': '',
    'Age': [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    'Gender': ["Male","Female"],
    'Dominant Eye': ["Right","Left"],
    'Dominant Hand': ["Right","Left"],
    'session': 'GF',
    'EDF Filename': '',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Define some variables which will change depending on pilot mode ---
'''
To run in pilot mode, either use the run/pilot toggle in Builder, Coder and Runner, 
or run the experiment with `--pilot` as an argument. To change what pilot 
#mode does, check out the 'Pilot mode' tab in preferences.
'''
# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()
# start off with values from experiment settings
_fullScr = True
_winSize = [1536, 864]
# if in pilot mode, apply overrides according to preferences
if PILOTING:
    # force windowed mode
    if prefs.piloting['forceWindowed']:
        _fullScr = False
        # set window size
        _winSize = prefs.piloting['forcedWindowSize']

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    Parameters
    ==========
    expInfo : dict
        Information about this experiment.
    
    Returns
    ==========
    dict
        Information about this experiment.
    """
    # show participant info dialog
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    # return expInfo
    return expInfo


def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    dataDir : Path, str or None
        Folder to save the data to, leave as None to create a folder in the current directory.    
    Returns
    ==========
    psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    # remove dialog-specific syntax from expInfo
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
    
    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data' + os.sep + '%s_%s' % (expInfo['participant'], expInfo['date'])
    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)
    
    # an ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(
        name=expName, version='',
        extraInfo=expInfo, runtimeInfo=None,
        originPath='E:\\PHD\\Punjabi\\pixels2preposition_far_near_lastrun.py',
        savePickle=True, saveWideText=True,
        dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    # return experiment handler
    return thisExp


def setupLogging(filename):
    """
    Setup a log file and tell it what level to log at.
    
    Parameters
    ==========
    filename : str or pathlib.Path
        Filename to save log file and data files as, doesn't need an extension.
    
    Returns
    ==========
    psychopy.logging.LogFile
        Text stream to receive inputs from the logging system.
    """
    # set how much information should be printed to the console / app
    if PILOTING:
        logging.console.setLevel(
            prefs.piloting['pilotConsoleLoggingLevel']
        )
    else:
        logging.console.setLevel('error')
    # save a log file for detail verbose info
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(
            prefs.piloting['pilotLoggingLevel']
        )
    else:
        logFile.setLevel(
            logging.getLevel('error')
        )
    
    return logFile


def setupWindow(expInfo=None, win=None):
    """
    Setup the Window
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    win : psychopy.visual.Window
        Window to setup - leave as None to create a new window.
    
    Returns
    ==========
    psychopy.visual.Window
        Window in which to run this experiment.
    """
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')
    
    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=0,
            winType='pyglet', allowStencil=True,
            monitor='testMonitor', color='1.0000, 1.0000, 1.0000', colorSpace='rgb',
            backgroundImage='', backgroundFit='none',
            blendMode='avg', useFBO=True,
            units='pix', 
            checkTiming=False  # we're going to do this ourselves in a moment
        )
    else:
        # if we have a window, just set the attributes which are safe to set
        win.color = '1.0000, 1.0000, 1.0000'
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'pix'
    if expInfo is not None:
        # get/measure frame rate if not already in expInfo
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='Attempting to measure frame rate of screen, please wait...')
        expInfo['frameRate'] = win._monitorFrameRate
    win.mouseVisible = False
    win.hideMessage()
    # show a visual indicator if we're in piloting mode
    if PILOTING and prefs.piloting['showPilotingIndicator']:
        win.showPilotingIndicator()
    
    return win


def setupDevices(expInfo, thisExp, win):
    """
    Setup whatever devices are available (mouse, keyboard, speaker, eyetracker, etc.) and add them to 
    the device manager (deviceManager)
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window in which to run this experiment.
    Returns
    ==========
    bool
        True if completed successfully.
    """
    # --- Setup input devices ---
    ioConfig = {}
    ioSession = ioServer = eyetracker = None
    
    # store ioServer object in the device manager
    deviceManager.ioServer = ioServer
    
    # create a default keyboard (e.g. to check for escape)
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='ptb'
        )
    if deviceManager.getDevice('key_resp') is None:
        # initialise key_resp
        key_resp = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='key_resp',
        )
    if deviceManager.getDevice('tr1_key_resp_instruct') is None:
        # initialise tr1_key_resp_instruct
        tr1_key_resp_instruct = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='tr1_key_resp_instruct',
        )
    if deviceManager.getDevice('key_resp_break') is None:
        # initialise key_resp_break
        key_resp_break = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='key_resp_break',
        )
    if deviceManager.getDevice('s1_key_resp_instruct') is None:
        # initialise s1_key_resp_instruct
        s1_key_resp_instruct = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='s1_key_resp_instruct',
        )
    if deviceManager.getDevice('key_resp_trial_break_2') is None:
        # initialise key_resp_trial_break_2
        key_resp_trial_break_2 = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='key_resp_trial_break_2',
        )
    # return True if completed successfully
    return True

def pauseExperiment(thisExp, win=None, timers=[], playbackComponents=[]):
    """
    Pause this experiment, preventing the flow from advancing to the next routine until resumed.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    timers : list, tuple
        List of timers to reset once pausing is finished.
    playbackComponents : list, tuple
        List of any components with a `pause` method which need to be paused.
    """
    # if we are not paused, do nothing
    if thisExp.status != PAUSED:
        return
    
    # start a timer to figure out how long we're paused for
    pauseTimer = core.Clock()
    # pause any playback components
    for comp in playbackComponents:
        comp.pause()
    # make sure we have a keyboard
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend='PsychToolbox',
        )
    # run a while loop while we wait to unpause
    while thisExp.status == PAUSED:
        # sleep 1ms so other threads can execute
        clock.time.sleep(0.001)
    # if stop was requested while paused, quit
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    # resume any playback components
    for comp in playbackComponents:
        comp.play()
    # reset any timers
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())


def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    """
    Run the experiment flow.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    psychopy.visual.Window
        Window in which to run this experiment.
    globalClock : psychopy.core.clock.Clock or None
        Clock to get global time from - supply None to make a new one.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    # mark experiment as started
    thisExp.status = STARTED
    # make sure variables created by exec are available globally
    exec = environmenttools.setExecEnvironment(globals())
    # get device handles from dict of input devices
    ioServer = deviceManager.ioServer
    # get/create a default keyboard (e.g. to check for escape)
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='PsychToolbox'
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    # make sure we're running in the directory for this experiment
    os.chdir(_thisDir)
    # get filename from ExperimentHandler for convenience
    filename = thisExp.dataFileName
    frameTolerance = 0.001  # how close to onset before 'same' frame
    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    # get frame duration from frame rate in expInfo
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess
    
    # Start Code - component code to be run after the window creation
    
    # --- Initialize components for Routine "init" ---
    # Run 'Begin Experiment' code from experiment_init
    delayDurMin = 0.1
    delayDurMax = 0.5
    
    # Fixation cross duration
    fixDurMin = 0.5 # minimum: 500 ms
    fixDurMax = 1 # maximum: 1000 ms
    
    # Time between trials
    iti = 0.5 # One second
    
    # Break after these many trials
    tr1_break = 36
    s1_break = 27
    
    #drift check after every n trials
    drift_interval = 10
    do_drift = False
    # Run 'Begin Experiment' code from button_init
    # %%
    keypress_text = "Please press any key to proceed."
    
    tr1_text_base = (
        "Please look at the fixation cross till the image appears.\n"
        f"Look at the image as long as it is on the screen.\n"
         
    )
    tr1_text = "Session 1\n\n" +  tr1_text_base + "\n" +keypress_text
    s1_text = "Session 2\n\n" + tr1_text_base + keypress_text
    tr2_text_base = (
    "Listen to the sentence. /n"
        "Please look at the fixation cross till the image appears.\n"
        f"Look at the image as long as it is on the screen.\n"
         )
    tr2_text =  tr2_text_base+ keypress_text
    s3_text = "Experiment Session\n\n" + tr2_text_base + keypress_text
    
    
    trial_break_message =""
    # This section of the EyeLink Initialize component code opens an EDF file,
    # writes some header text to the file, and configures some tracker settings
    el_tracker = pylink.getEYELINK()
    global edf_fname
    # Open an EDF data file on the Host PC
    edf_file = edf_fname + ".EDF"
    try:
        el_tracker.openDataFile(edf_file)
    except RuntimeError as err:
        print("ERROR:", err)
        # close the link if we have one open
        if el_tracker.isConnected():
            el_tracker.close()
        core.quit()
        sys.exit()
    
    # Add a header text to the EDF file to identify the current experiment name
    # This is OPTIONAL. If your text starts with "RECORDED BY " it will be
    # available in DataViewer's Inspector window by clicking
    # the EDF session node in the top panel and looking for the "Recorded By:"
    # field in the bottom panel of the Inspector.
    preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
    el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)
    
    # Configure the tracker
    #
    # Put the tracker in offline mode before we change tracking parameters
    el_tracker.setOfflineMode()
    
    # Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
    # 5-EyeLink 1000 Plus, 6-Portable DUO
    eyelink_ver = 0  # set version to 0, in case running in Dummy mode
    if not dummy_mode:
        vstr = el_tracker.getTrackerVersionString()
        eyelink_ver = int(vstr.split()[-1].split(".")[0])
        # print out some version info in the shell
        print("Running experiment on %s, version %d" % (vstr, eyelink_ver))
    
    # File and Link data control
    # what eye events to save in the EDF file, include everything by default
    file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
    # what eye events to make available over the link, include everything by default
    link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
    # what sample data to save in the EDF data file and to make available
    # over the link, include the 'HTARGET' flag to save head target sticker
    # data for supported eye trackers
    if eyelink_ver > 3:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
    else:
        file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
        link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
    el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
    el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
    el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
    el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)
    # Set a gamepad button to accept calibration/drift check target
    # You need a supported gamepad/button box that is connected to the Host PC
    el_tracker.sendCommand("button_function 5 'accept_target_fixation'")
    
    global eyelinkThisFrameCallOnFlipScheduled,eyelinkLastFlipTime,zeroTimeDLF,sentDrawListMessage,zeroTimeIAS,sentIASFileMessage
    
    # --- Initialize components for Routine "eyelinkSetup" ---
    elInstructions = visual.TextStim(win=win, name='elInstructions',
        text='Press any key to start Camera Setup',
        font='Open Sans',
        pos=(0, 0), draggable=False, height=50.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    key_resp = keyboard.Keyboard(deviceName='key_resp')
    Initialize = event.Mouse(win=win)
    CameraSetup = event.Mouse(win=win)
    
    # --- Initialize components for Routine "TR1_instruct" ---
    tr1_textbox_instruct = visual.TextBox2(
         win, text=tr1_text, placeholder='Type here...', font='Times New Roman',
         ori=0.0, pos=(0, 0), draggable=False, units='height',     letterHeight=0.05,
         size=(2, 2), borderWidth=2.0,
         color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb',
         opacity=None,
         bold=False, italic=False,
         lineSpacing=1.0, speechPoint=None,
         padding=0.0, alignment='center',
         anchor='center', overflow='visible',
         fillColor=None, borderColor=None,
         flipHoriz=False, flipVert=False, languageStyle='LTR',
         editable=False,
         name='tr1_textbox_instruct',
         depth=0, autoLog=True,
    )
    tr1_key_resp_instruct = keyboard.Keyboard(deviceName='tr1_key_resp_instruct')
    
    # --- Initialize components for Routine "Good_to_go" ---
    text = visual.TextStim(win=win, name='text',
        text='Experiment Starts.\nKeep eyes on screen at all times.',
        font='Times New Roman',
        units='height', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    
    # --- Initialize components for Routine "TR1_eyelink_start" ---
    HostDrawing = event.Mouse(win=win)
    DriftCheck = event.Mouse(win=win)
    StartRecord = event.Mouse(win=win)
    
    # --- Initialize components for Routine "TR1_image_display" ---
    tr1_crosshair = visual.TextStim(win=win, name='tr1_crosshair',
        text='+',
        font='Arial',
        units='height', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    tr1_image = visual.ImageStim(
        win=win,
        name='tr1_image', 
        image='default.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(1080, 1080),
        color=[1.0000, 1.0000, 1.0000], colorSpace='rgb', opacity=None,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=-2.0)
    MarkEvents = event.Mouse(win=win)
    
    # --- Initialize components for Routine "TR1_eyelink_stop" ---
    StopRecord = event.Mouse(win=win)
    
    # --- Initialize components for Routine "inter_trial_interval" ---
    blank_iti = visual.TextStim(win=win, name='blank_iti',
        text=None,
        font='Arial',
        pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    
    # --- Initialize components for Routine "Break" ---
    break_text = visual.TextStim(win=win, name='break_text',
        text='Training Session Ends.\nAfter re-caliberation the trial Session will start.\n',
        font='Times New Roman',
        units='height', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    key_resp_break = keyboard.Keyboard(deviceName='key_resp_break')
    
    # --- Initialize components for Routine "Trial_calib" ---
    CameraSetup_3 = event.Mouse(win=win)
    
    # --- Initialize components for Routine "S1_instruct" ---
    s1_textbox_instruct = visual.TextBox2(
         win, text=s1_text, placeholder='Type here...', font='Times New Roman',
         ori=0.0, pos=(0, 0), draggable=False, units='height',     letterHeight=0.05,
         size=(2, 2), borderWidth=2.0,
         color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb',
         opacity=None,
         bold=False, italic=False,
         lineSpacing=1.0, speechPoint=None,
         padding=0.0, alignment='center',
         anchor='center', overflow='visible',
         fillColor=None, borderColor=None,
         flipHoriz=False, flipVert=False, languageStyle='LTR',
         editable=False,
         name='s1_textbox_instruct',
         depth=0, autoLog=True,
    )
    s1_key_resp_instruct = keyboard.Keyboard(deviceName='s1_key_resp_instruct')
    
    # --- Initialize components for Routine "S1_Break" ---
    textbox_break_2 = visual.TextBox2(
         win, text='', placeholder='Type here...', font='Times New Roman',
         ori=0.0, pos=(0, 0), draggable=False, units='height',     letterHeight=0.05,
         size=(2, 2), borderWidth=2.0,
         color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb',
         opacity=None,
         bold=False, italic=False,
         lineSpacing=1.0, speechPoint=None,
         padding=0.0, alignment='center',
         anchor='center', overflow='visible',
         fillColor=None, borderColor=None,
         flipHoriz=False, flipVert=False, languageStyle='LTR',
         editable=False,
         name='textbox_break_2',
         depth=-1, autoLog=True,
    )
    timer_clock_trial_2 = visual.TextStim(win=win, name='timer_clock_trial_2',
        text='',
        font='Times New Roman',
        units='height', pos=(0, -0.1), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-2.0);
    key_resp_trial_break_2 = keyboard.Keyboard(deviceName='key_resp_trial_break_2')
    
    # --- Initialize components for Routine "S1_eyelink_start" ---
    HostDrawing_2 = event.Mouse(win=win)
    DriftCheck_2 = event.Mouse(win=win)
    StartRecord_2 = event.Mouse(win=win)
    
    # --- Initialize components for Routine "S1_image_display" ---
    s1_crosshair = visual.TextStim(win=win, name='s1_crosshair',
        text='+',
        font='Arial',
        units='height', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    s1_image = visual.ImageStim(
        win=win,
        name='s1_image', 
        image='default.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(1080, 1080),
        color=[1.0000, 1.0000, 1.0000], colorSpace='rgb', opacity=None,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=-2.0)
    movie = visual.MovieStim(
        win, name='movie',
        filename=None, movieLib='ffpyplayer',
        loop=False, volume=1.0, noAudio=False,
        pos=(0, 0), size=(0.5, 0.5), units=win.units,
        ori=0.0, anchor='center',opacity=None, contrast=1.0,
        depth=-3
    )
    MarkEvents_2 = event.Mouse(win=win)
    
    # --- Initialize components for Routine "S1_eye_link_stop" ---
    StopRecord_2 = event.Mouse(win=win)
    
    # --- Initialize components for Routine "inter_trial_interval" ---
    blank_iti = visual.TextStim(win=win, name='blank_iti',
        text=None,
        font='Arial',
        pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    
    # --- Initialize components for Routine "thanks" ---
    textbox = visual.TextBox2(
         win, text='Thank you for your participation.\nPlease fill the post experiment survey', placeholder='Type here...', font='Times New Roman',
         ori=0.0, pos=(0, 0), draggable=False, units='height',     letterHeight=0.05,
         size=(2, 2), borderWidth=2.0,
         color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb',
         opacity=None,
         bold=False, italic=False,
         lineSpacing=1.0, speechPoint=None,
         padding=0.0, alignment='center',
         anchor='center', overflow='visible',
         fillColor=None, borderColor=None,
         flipHoriz=False, flipVert=False, languageStyle='LTR',
         editable=False,
         name='textbox',
         depth=0, autoLog=True,
    )
    
    # create some handy timers
    
    # global clock to track the time since experiment started
    if globalClock is None:
        # create a clock if not given one
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        # if given a string, make a clock accoridng to it
        if globalClock == 'float':
            # get timestamps as a simple value
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            # get timestamps in ISO format
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            # get timestamps in a custom format
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    # routine timer to track time remaining of each (possibly non-slip) routine
    routineTimer = core.Clock()
    win.flip()  # flip window to reset last flip timer
    # store the exact time the global clock started
    expInfo['expStart'] = data.getDateStr(
        format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6
    )
    
    # --- Prepare to start Routine "init" ---
    # create an object to store info about Routine init
    init = data.Routine(
        name='init',
        components=[],
    )
    init.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # store start times for init
    init.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    init.tStart = globalClock.getTime(format='float')
    init.status = STARTED
    thisExp.addData('init.started', init.tStart)
    init.maxDuration = None
    # keep track of which components have finished
    initComponents = init.components
    for thisComponent in init.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "init" ---
    init.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            init.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in init.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "init" ---
    for thisComponent in init.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for init
    init.tStop = globalClock.getTime(format='float')
    init.tStopRefresh = tThisFlipGlobal
    thisExp.addData('init.stopped', init.tStop)
    thisExp.nextEntry()
    # the Routine "init" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "eyelinkSetup" ---
    # create an object to store info about Routine eyelinkSetup
    eyelinkSetup = data.Routine(
        name='eyelinkSetup',
        components=[elInstructions, key_resp, Initialize, CameraSetup],
    )
    eyelinkSetup.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for key_resp
    key_resp.keys = []
    key_resp.rt = []
    _key_resp_allKeys = []
    # store start times for eyelinkSetup
    eyelinkSetup.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    eyelinkSetup.tStart = globalClock.getTime(format='float')
    eyelinkSetup.status = STARTED
    thisExp.addData('eyelinkSetup.started', eyelinkSetup.tStart)
    eyelinkSetup.maxDuration = None
    # keep track of which components have finished
    eyelinkSetupComponents = eyelinkSetup.components
    for thisComponent in eyelinkSetup.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "eyelinkSetup" ---
    eyelinkSetup.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *elInstructions* updates
        
        # if elInstructions is starting this frame...
        if elInstructions.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            elInstructions.frameNStart = frameN  # exact frame index
            elInstructions.tStart = t  # local t and not account for scr refresh
            elInstructions.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(elInstructions, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'elInstructions.started')
            # update status
            elInstructions.status = STARTED
            elInstructions.setAutoDraw(True)
        
        # if elInstructions is active this frame...
        if elInstructions.status == STARTED:
            # update params
            pass
        
        # *key_resp* updates
        waitOnFlip = False
        
        # if key_resp is starting this frame...
        if key_resp.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            key_resp.frameNStart = frameN  # exact frame index
            key_resp.tStart = t  # local t and not account for scr refresh
            key_resp.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(key_resp, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'key_resp.started')
            # update status
            key_resp.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(key_resp.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(key_resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if key_resp.status == STARTED and not waitOnFlip:
            theseKeys = key_resp.getKeys(keyList=None, ignoreKeys=None, waitRelease=False)
            _key_resp_allKeys.extend(theseKeys)
            if len(_key_resp_allKeys):
                key_resp.keys = _key_resp_allKeys[-1].name  # just the last key pressed
                key_resp.rt = _key_resp_allKeys[-1].rt
                key_resp.duration = _key_resp_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            eyelinkSetup.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in eyelinkSetup.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "eyelinkSetup" ---
    for thisComponent in eyelinkSetup.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for eyelinkSetup
    eyelinkSetup.tStop = globalClock.getTime(format='float')
    eyelinkSetup.tStopRefresh = tThisFlipGlobal
    thisExp.addData('eyelinkSetup.stopped', eyelinkSetup.tStop)
    # check responses
    if key_resp.keys in ['', [], None]:  # No response was made
        key_resp.keys = None
    thisExp.addData('key_resp.keys',key_resp.keys)
    if key_resp.keys != None:  # we had a response
        thisExp.addData('key_resp.rt', key_resp.rt)
        thisExp.addData('key_resp.duration', key_resp.duration)
    # This section of the EyeLink Initialize component code gets graphic 
    # information from Psychopy, sets the screen_pixel_coords on the Host PC based
    # on these values, and logs the screen resolution for Data Viewer via 
    # a DISPLAY_COORDS message
    
    # get the native screen resolution used by PsychoPy
    scn_width, scn_height = win.size
    # resolution fix for Mac retina displays
    if 'Darwin' in platform.system():
        if use_retina:
            scn_width = int(scn_width/2.0)
            scn_height = int(scn_height/2.0)
    
    # Pass the display pixel coordinates (left, top, right, bottom) to the tracker
    # see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)
    
    # Write a DISPLAY_COORDS message to the EDF file
    # Data Viewer needs this piece of info for proper visualization, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendMessage(dv_coords)# This Begin Experiment tab of the elTrial component just initializes
    # a trial counter variable at the beginning of the experiment
    trial_index = 1
    # Configure a graphics environment (genv) for tracker calibration
    genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win, False)
    print(genv)  # print out the version number of the CoreGraphics library
    
    # resolution fix for macOS retina display issues
    if use_retina:
        genv.fixMacRetinaDisplay()
    # Request Pylink to use the PsychoPy window we opened above for calibration
    pylink.openGraphicsEx(genv)
    # Create an array of pixels to assist in transferring content to the Host PC backdrop
    rgbBGColor = eyelink_color(win.color)
    blankHostPixels = [[rgbBGColor for i in range(scn_width)]
        for j in range(scn_height)]
    # This section of EyeLink CameraSetup component code configures some
    # graphics options for calibration, and then performs a camera setup
    # so that you can set up the eye tracker and calibrate/validate the participant
    # graphics options for calibration, and then performs a camera setup
    # so that you can set up the eye tracker and calibrate/validate the participant
    
    # Set background and foreground colors for the calibration target
    # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
    background_color = (1, 1, 1)
    foreground_color = (0,0,0)
    genv.setCalibrationColors(foreground_color, background_color)
    
    # Set up the calibration/validation target
    #
    # The target could be a "circle" (default), a "picture", a "movie" clip,
    # or a rotating "spiral". To configure the type of drift check target, set
    # genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
    genv.setTargetType('picture')
    #
    # Use a picture as the drift check target
    # Use genv.setPictureTarget() to set a "movie" target
    genv.setPictureTarget(os.path.normpath('images/fixTarget2.png'))
    
    # Beeps to play during calibration, validation and drift correction
    # parameters: target, good, error
    #     target -- sound to play when target moves
    #     good -- sound to play on successful operation
    #     error -- sound to play on failure or interruption
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    genv.setCalibrationSounds('', '', '')
    
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    el_tracker.sendCommand("calibration_type = " 'HV9')
    #clear the screen before we begin Camera Setup mode
    clear_screen(win,genv)
    
    
    # Go into Camera Setup mode so that participant setup/EyeLink calibration/validation can be performed
    # skip this step if running the script in Dummy Mode
    if not dummy_mode:
        try:
            el_tracker.doTrackerSetup()
        except RuntimeError as err:
            print('ERROR:', err)
            el_tracker.exitCalibration()
        else:
            win.mouseVisible = False
    thisExp.nextEntry()
    # the Routine "eyelinkSetup" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "TR1_instruct" ---
    # create an object to store info about Routine TR1_instruct
    TR1_instruct = data.Routine(
        name='TR1_instruct',
        components=[tr1_textbox_instruct, tr1_key_resp_instruct],
    )
    TR1_instruct.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    tr1_textbox_instruct.reset()
    # create starting attributes for tr1_key_resp_instruct
    tr1_key_resp_instruct.keys = []
    tr1_key_resp_instruct.rt = []
    _tr1_key_resp_instruct_allKeys = []
    # store start times for TR1_instruct
    TR1_instruct.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    TR1_instruct.tStart = globalClock.getTime(format='float')
    TR1_instruct.status = STARTED
    thisExp.addData('TR1_instruct.started', TR1_instruct.tStart)
    TR1_instruct.maxDuration = None
    # keep track of which components have finished
    TR1_instructComponents = TR1_instruct.components
    for thisComponent in TR1_instruct.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "TR1_instruct" ---
    TR1_instruct.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *tr1_textbox_instruct* updates
        
        # if tr1_textbox_instruct is starting this frame...
        if tr1_textbox_instruct.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            tr1_textbox_instruct.frameNStart = frameN  # exact frame index
            tr1_textbox_instruct.tStart = t  # local t and not account for scr refresh
            tr1_textbox_instruct.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(tr1_textbox_instruct, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'tr1_textbox_instruct.started')
            # update status
            tr1_textbox_instruct.status = STARTED
            tr1_textbox_instruct.setAutoDraw(True)
        
        # if tr1_textbox_instruct is active this frame...
        if tr1_textbox_instruct.status == STARTED:
            # update params
            pass
        
        # *tr1_key_resp_instruct* updates
        waitOnFlip = False
        
        # if tr1_key_resp_instruct is starting this frame...
        if tr1_key_resp_instruct.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            tr1_key_resp_instruct.frameNStart = frameN  # exact frame index
            tr1_key_resp_instruct.tStart = t  # local t and not account for scr refresh
            tr1_key_resp_instruct.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(tr1_key_resp_instruct, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'tr1_key_resp_instruct.started')
            # update status
            tr1_key_resp_instruct.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(tr1_key_resp_instruct.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(tr1_key_resp_instruct.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if tr1_key_resp_instruct.status == STARTED and not waitOnFlip:
            theseKeys = tr1_key_resp_instruct.getKeys(keyList=None, ignoreKeys=None, waitRelease=False)
            _tr1_key_resp_instruct_allKeys.extend(theseKeys)
            if len(_tr1_key_resp_instruct_allKeys):
                tr1_key_resp_instruct.keys = _tr1_key_resp_instruct_allKeys[-1].name  # just the last key pressed
                tr1_key_resp_instruct.rt = _tr1_key_resp_instruct_allKeys[-1].rt
                tr1_key_resp_instruct.duration = _tr1_key_resp_instruct_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            TR1_instruct.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in TR1_instruct.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "TR1_instruct" ---
    for thisComponent in TR1_instruct.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for TR1_instruct
    TR1_instruct.tStop = globalClock.getTime(format='float')
    TR1_instruct.tStopRefresh = tThisFlipGlobal
    thisExp.addData('TR1_instruct.stopped', TR1_instruct.tStop)
    # check responses
    if tr1_key_resp_instruct.keys in ['', [], None]:  # No response was made
        tr1_key_resp_instruct.keys = None
    thisExp.addData('tr1_key_resp_instruct.keys',tr1_key_resp_instruct.keys)
    if tr1_key_resp_instruct.keys != None:  # we had a response
        thisExp.addData('tr1_key_resp_instruct.rt', tr1_key_resp_instruct.rt)
        thisExp.addData('tr1_key_resp_instruct.duration', tr1_key_resp_instruct.duration)
    thisExp.nextEntry()
    # the Routine "TR1_instruct" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "Good_to_go" ---
    # create an object to store info about Routine Good_to_go
    Good_to_go = data.Routine(
        name='Good_to_go',
        components=[text],
    )
    Good_to_go.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # store start times for Good_to_go
    Good_to_go.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Good_to_go.tStart = globalClock.getTime(format='float')
    Good_to_go.status = STARTED
    thisExp.addData('Good_to_go.started', Good_to_go.tStart)
    Good_to_go.maxDuration = None
    # keep track of which components have finished
    Good_to_goComponents = Good_to_go.components
    for thisComponent in Good_to_go.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "Good_to_go" ---
    Good_to_go.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 2.0:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *text* updates
        
        # if text is starting this frame...
        if text.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            text.frameNStart = frameN  # exact frame index
            text.tStart = t  # local t and not account for scr refresh
            text.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(text, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'text.started')
            # update status
            text.status = STARTED
            text.setAutoDraw(True)
        
        # if text is active this frame...
        if text.status == STARTED:
            # update params
            pass
        
        # if text is stopping this frame...
        if text.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > text.tStartRefresh + 2-frameTolerance:
                # keep track of stop time/frame for later
                text.tStop = t  # not accounting for scr refresh
                text.tStopRefresh = tThisFlipGlobal  # on global time
                text.frameNStop = frameN  # exact frame index
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'text.stopped')
                # update status
                text.status = FINISHED
                text.setAutoDraw(False)
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            Good_to_go.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in Good_to_go.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "Good_to_go" ---
    for thisComponent in Good_to_go.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Good_to_go
    Good_to_go.tStop = globalClock.getTime(format='float')
    Good_to_go.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Good_to_go.stopped', Good_to_go.tStop)
    # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
    if Good_to_go.maxDurationReached:
        routineTimer.addTime(-Good_to_go.maxDuration)
    elif Good_to_go.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-2.000000)
    thisExp.nextEntry()
    
    # set up handler to look after randomisation of conditions etc
    free_view_loop = data.TrialHandler2(
        name='free_view_loop',
        nReps=1.0, 
        method='fullRandom', 
        extraInfo=expInfo, 
        originPath=-1, 
        trialList=data.importConditions('exp_files/experiment_data.csv'), 
        seed=None, 
    )
    thisExp.addLoop(free_view_loop)  # add the loop to the experiment
    thisFree_view_loop = free_view_loop.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisFree_view_loop.rgb)
    if thisFree_view_loop != None:
        for paramName in thisFree_view_loop:
            globals()[paramName] = thisFree_view_loop[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    
    for thisFree_view_loop in free_view_loop:
        currentLoop = free_view_loop
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisFree_view_loop.rgb)
        if thisFree_view_loop != None:
            for paramName in thisFree_view_loop:
                globals()[paramName] = thisFree_view_loop[paramName]
        
        # --- Prepare to start Routine "TR1_eyelink_start" ---
        # create an object to store info about Routine TR1_eyelink_start
        TR1_eyelink_start = data.Routine(
            name='TR1_eyelink_start',
            components=[HostDrawing, DriftCheck, StartRecord],
        )
        TR1_eyelink_start.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for TR1_eyelink_start
        TR1_eyelink_start.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        TR1_eyelink_start.tStart = globalClock.getTime(format='float')
        TR1_eyelink_start.status = STARTED
        thisExp.addData('TR1_eyelink_start.started', TR1_eyelink_start.tStart)
        TR1_eyelink_start.maxDuration = None
        # keep track of which components have finished
        TR1_eyelink_startComponents = TR1_eyelink_start.components
        for thisComponent in TR1_eyelink_start.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "TR1_eyelink_start" ---
        # if trial has changed, end Routine now
        if isinstance(free_view_loop, data.TrialHandler2) and thisFree_view_loop.thisN != free_view_loop.thisTrial.thisN:
            continueRoutine = False
        TR1_eyelink_start.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 0.001:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                TR1_eyelink_start.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in TR1_eyelink_start.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "TR1_eyelink_start" ---
        for thisComponent in TR1_eyelink_start.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for TR1_eyelink_start
        TR1_eyelink_start.tStop = globalClock.getTime(format='float')
        TR1_eyelink_start.tStopRefresh = tThisFlipGlobal
        thisExp.addData('TR1_eyelink_start.stopped', TR1_eyelink_start.tStop)
        # This section of EyeLink HostDrawing component code provides options for sending images/shapes
        # representing stimuli to the Host PC backdrop for real-time gaze monitoring
        
        # get a reference to the currently active EyeLink connection
        el_tracker = pylink.getEYELINK()
        # put the tracker in the offline mode first
        el_tracker.setOfflineMode()
        # clear the host screen before we draw the backdrop
        el_tracker.sendCommand('clear_screen 0')
        # imagesAndComponentsStringList value = ['file,tr1_image']
        # Send image components to the Host PC backdrop to serve as landmarks during recording
        # The method bitmapBackdrop() requires a step of converting the
        # image pixels into a recognizable format by the Host PC.
        # pixels = [line1, ...lineH], line = [pix1,...pixW], pix=(R,G,B)
        # the bitmapBackdrop() command takes time to return, not recommended
        # for tasks where the ITI matters, e.g., in an event-related fMRI task
        # parameters: width, height, pixel, crop_x, crop_y,
        #             crop_width, crop_height, x, y on the Host, drawing options
        imagesAndComponentsListForHostBackdrop = [[file, tr1_image]]
        # get the array of blank pixels where each pixel corresponds to win.color
        pixels = blankHostPixels[::]
        # go through each image and replace the pixels in the blank array with the image pixels
        for thisImage in imagesAndComponentsListForHostBackdrop:
            thisImageFile = thisImage[0]
            thisImageComponent = thisImage[1]
            thisImageComponent.setImage(thisImageFile)
            if "Image" in str(thisImageComponent.__class__):
                # Use the code commented below to convert the image and send the backdrop
                im = Image.open(script_path + "/" + thisImageFile)
                thisImageComponent.elPos = eyelink_pos(thisImageComponent.pos,[scn_width,scn_height])
                thisImageComponent.elSize = eyelink_size(thisImageComponent.size,[scn_width,scn_height])
                imWidth = int(round(thisImageComponent.elSize[0]))
                imHeight = int(round(thisImageComponent.elSize[1]))
                imLeft = int(round(thisImageComponent.elPos[0]-thisImageComponent.elSize[0]/2))
                imTop = int(round(thisImageComponent.elPos[1]-thisImageComponent.elSize[1]/2))
                im = im.resize((imWidth,imHeight))
                # Access the pixel data of the image
                img_pixels = list(im.getdata())
                # Check to see if the image goes off the screen
                # If so, adjust the coordinates appropriately
                if imLeft < 0:
                    imTransferLeft = 0
                else:
                    imTransferLeft = imLeft
                if imTop < 0:
                    imTransferTop = 0
                else:
                    imTransferTop = imTop
                if imLeft + imWidth > scn_width:
                    imTransferRight = scn_width
                else:
                    imTransferRight = imLeft+imWidth
                if imTop + imHeight > scn_height:
                    imTransferBottom = scn_height
                else:
                    imTransferBottom = imTop+imHeight    
                imTransferImageLineStartX = imTransferLeft-imLeft
                imTransferImageLineEndX = imTransferRight-imTransferLeft+imTransferImageLineStartX
                imTransferImageLineStartY = imTransferTop-imTop
                for y in range(imTransferBottom-imTransferTop):
                    pixels[imTransferTop+y][imTransferLeft:imTransferRight] = \
                        img_pixels[(imTransferImageLineStartY + y)*imWidth+imTransferImageLineStartX:\
                        (imTransferImageLineStartY + y)*imWidth + imTransferImageLineEndX]
            else:
                print("WARNING: Image Transfer Not Supported For non-Image Component %s)" % str(thisComponent.__class__))
        # transfer the full-screen pixel array to the Host PC
        el_tracker.bitmapBackdrop(scn_width,scn_height, pixels,\
            0, 0, scn_width, scn_height, 0, 0, pylink.BX_MAXCONTRAST)
        # Draw rectangles along the edges of components to serve as landmarks on the Host PC backdrop during recording
        # For a list of supported draw commands, see the "COMMANDS.INI" file on the Host PC
        componentDrawListForHostBackdrop = [tr1_crosshair]
        for thisComponent in componentDrawListForHostBackdrop:
                thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                drawColor = 4
                drawCommand = "draw_box = %i %i %i %i %i" % (thisComponent.elPos[0] - thisComponent.elSize[0]/2,
                    thisComponent.elPos[1] - thisComponent.elSize[1]/2, thisComponent.elPos[0] + thisComponent.elSize[0]/2,
                    thisComponent.elPos[1] + thisComponent.elSize[1]/2, drawColor)
                el_tracker.sendCommand(drawCommand)
        # record_status_message -- send a messgae string to the Host PC that will be present during recording
        el_tracker.sendCommand("record_status_message '%s'" % ("Trial %s" % trial_index))
        # This section of EyeLink DriftCheck component code configures some
        # graphics options for drift check, and then performs the drift check
        # Set background and foreground colors for the drift check target
        # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
        background_color = (1,1,1)
        foreground_color = (0,0,0)
        genv.setCalibrationColors(foreground_color, background_color)
        # Set up the drift check target
        # The target could be a "circle" (default), a "picture", a "movie" clip,
        # or a rotating "spiral". To configure the type of drift check target, set
        # genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
        genv.setTargetType('picture')
        # Use a picture as the drift check target
        # Use genv.setPictureTarget() to set a "movie" target
        genv.setPictureTarget(os.path.normpath('images/fixTarget2.png'))
        # Beeps to play during calibration, validation and drift correction
        # parameters: target, good, error
        #     target -- sound to play when target moves
        #     good -- sound to play on successful operation
        #     error -- sound to play on failure or interruption
        # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
        genv.setCalibrationSounds('', '', '')
        
        # drift check
        # the doDriftCorrect() function requires target position in integers
        # the last two arguments:
        # draw_target (1-default, 0-draw the target then call doDriftCorrect)
        # allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
        
        # Skip drift-check if running the script in Dummy Mode
        while not dummy_mode:
            # terminate the task if no longer connected to the tracker or
            # user pressed Ctrl-C to terminate the task
            if (not el_tracker.isConnected()) or el_tracker.breakPressed():
                terminate_task(win,genv,edf_file,session_folder,session_identifier)
            # drift-check and re-do camera setup if ESCAPE is pressed
            dcX,dcY = eyelink_pos([0,0],[scn_width,scn_height])
            try:
                error = el_tracker.doDriftCorrect(int(round(dcX)),int(round(dcY)),1,1)
                # break following a success drift-check
                if error is not pylink.ESC_KEY:
                    break
            except:
                pass
        # This section of EyeLink StartRecord component code starts eye tracker recording,
        # sends a trial start (i.e., TRIALID) message to the EDF, 
        # and logs which eye is tracked
        
        # get a reference to the currently active EyeLink connection
        el_tracker = pylink.getEYELINK()
        # Send a "TRIALID" message to mark the start of a trial, see the following Data Viewer User Manual:
        # "Protocol for EyeLink Data to Viewer Integration -> Defining the Start and End of a Trial"
        el_tracker.sendMessage('TRIALID %d' % trial_index)
        # Log the trial index at the start of recording in case there will be multiple trials within one recording
        trialIDAtRecordingStart = int(trial_index)
        # Log the routine index at the start of recording in case there will be multiple routines within one recording
        routine_index = 1
        # put tracker in idle/offline mode before recording
        el_tracker.setOfflineMode()
        # Start recording, logging all samples/events to the EDF and making all data available over the link
        # arguments: sample_to_file, events_to_file, sample_over_link, events_over_link (1-yes, 0-no)
        try:
            el_tracker.startRecording(1, 1, 1, 1)
        except RuntimeError as error:
            print("ERROR:", error)
            abort_trial(genv)
        # Allocate some time for the tracker to cache some samples before allowing
        # trial stimulus presentation to proceed
        pylink.pumpDelay(100)
        # determine which eye(s) is/are available
        # 0-left, 1-right, 2-binocular
        eye_used = el_tracker.eyeAvailable()
        if eye_used == 1:
            el_tracker.sendMessage("EYE_USED 1 RIGHT")
        elif eye_used == 0 or eye_used == 2:
            el_tracker.sendMessage("EYE_USED 0 LEFT")
            eye_used = 0
        else:
            print("ERROR: Could not get eye information!")
        #routineForceEnded = True
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if TR1_eyelink_start.maxDurationReached:
            routineTimer.addTime(-TR1_eyelink_start.maxDuration)
        elif TR1_eyelink_start.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-0.001000)
        
        # --- Prepare to start Routine "TR1_image_display" ---
        # create an object to store info about Routine TR1_image_display
        TR1_image_display = data.Routine(
            name='TR1_image_display',
            components=[tr1_crosshair, tr1_image, MarkEvents],
        )
        TR1_image_display.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from code
        # Fixation cross duration for this trial
        fixDur = np.random.uniform(fixDurMin, fixDurMax) # random between minimum and maximum
        thisExp.addData('fixation_duration',fixDur) # docu
        
        tr1_image.setImage(file)
        # This section of EyeLink MarkEvents component code initializes some variables that will help with
        # sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
        # sending DV Target Position Messages, and/or logging DV video frame marking info
        # information
        
        
        # log trial variables' values to the EDF data file, for details, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        trialConditionVariablesForEyeLinkLogging = [file,near_far,real_near_far_label,relation_correct,]
        trialConditionVariableNamesForEyeLinkLogging = ['file', 'near_far', 'real_near_far_label', 'relation_correct', '']
        for i in range(len(trialConditionVariablesForEyeLinkLogging)):
            el_tracker.sendMessage('!V TRIAL_VAR %s %s'% (trialConditionVariableNamesForEyeLinkLogging[i],trialConditionVariablesForEyeLinkLogging[i]))
            #add a brief pause after every 5 messages or so to make sure no messages are missed
            if i % 5 == 0:
                time.sleep(0.001)
        
        # list of all stimulus components whose onset/offset will be marked with messages
        componentsForEyeLinkStimEventMessages = [tr1_crosshair,tr1_image]
        # list of all stimulus components for which Data Viewer draw commands will be sent
        componentsForEyeLinkStimDVDrawingMessages = [tr1_crosshair,tr1_image]
        # list of all stimulus components which will have interest areas automatically created for them
        componentsForEyeLinkInterestAreaMessages = [tr1_crosshair]
        # create list of all components to be monitored for EyeLink Marking/Messaging
        allStimComponentsForEyeLinkMonitoring = componentsForEyeLinkStimEventMessages + componentsForEyeLinkStimDVDrawingMessages + componentsForEyeLinkInterestAreaMessages# make sure each component is only in the list once
        allStimComponentsForEyeLinkMonitoring = [*set(allStimComponentsForEyeLinkMonitoring)]
        # list of all response components whose onsets need to be marked and values
        # need to be logged
        componentsForEyeLinkRespEventMessages = [tr1_key_resp]
        
        # Initialize stimulus components whose occurence needs to be monitored for event
        # marking, Data Viewer integration, and/or interest area messaging
        # to the EDF (provided they are supported stimulus types)
        for thisComponent in allStimComponentsForEyeLinkMonitoring:
            componentClassString = str(thisComponent.__class__)
            supportedStimType = False
            for stimType in ["Aperture","Text","Dot","Shape","Rect","Grating","Image","MovieStim3","Movie","sound"]:
                if stimType in componentClassString:
                    supportedStimType = True
                    thisComponent.elOnsetDetected = False
                    thisComponent.elOffsetDetected = False
                    if thisComponent in componentsForEyeLinkInterestAreaMessages:
                        thisComponent.iaInstanceStartTime = -1
                        thisComponent.iaIndex = componentsForEyeLinkInterestAreaMessages.index(thisComponent) + 1
                    if stimType != "sound":
                        thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                        thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                        thisComponent.lastelPos = thisComponent.elPos
                        thisComponent.lastelSize = thisComponent.elSize
                    if stimType == "MovieStim3":
                        thisComponent.componentType = "MovieStim3"
                        thisComponent.elMarkingFrameIndex = -1
                        thisComponent.previousFrameTime = 0
                        thisComponent.firstFramePresented = False
                    elif stimType == "Movie":
                        thisComponent.componentType = "MovieStimWithFrameNum"
                        thisComponent.elMarkingFrameIndex = -1
                        thisComponent.firstFramePresented = False
                    else:
                        thisComponent.componentType = stimType
                    break   
            if not supportedStimType:
                print("WARNING:  Stimulus component type " + str(thisComponent.__class__) + " not supported for EyeLink event marking")
                print("          Event timing messages and/or Data Viewer drawing messages")
                print("          will not be marked for this component")
                print("          Consider marking the component via code component")
                # remove unsupported types from our monitoring lists
                allStimComponentsForEyeLinkMonitoring.remove(thisComponent)
                componentsForEyeLinkStimEventMessages.remove(thisComponent)
                componentsForEyeLinkStimDVDrawingMessages.remove(thisComponent)
                componentsForEyeLinkInterestAreaMessages.remove(thisComponent)
        
        # Set Interest Area Margin -- this value will be added to all four edges of the components
        # for which interest areas will be created
        interestAreaMargins = 0
        
        # Initialize response components whose occurence needs to be marked with 
        # a message to the EDF (provided they are supported stimulus types)
        # Supported types include mouse, keyboard, and any response component with an RT or time property
        for thisComponent in componentsForEyeLinkRespEventMessages:
            componentClassString = str(thisComponent.__class__)
            componentClassDir = dir(thisComponent)
            supportedRespType = False
            for respType in ["Mouse","Keyboard"]:
                if respType in componentClassString:
                    thisComponent.componentType = respType
                    supportedRespType = True
                    break
            if not supportedRespType:
                if "rt" in componentClassDir:
                    thisComponent.componentType = "OtherRespWithRT"
                    supportedRespType = True
                elif "time" in componentClassDir:
                    thisComponent.componentType = "OtherRespWithTime"
                    supportedRespType = True
            if not supportedRespType:    
                    print("WARNING:  Response component type " + str(thisComponent.__class__) + " not supported for EyeLink event marking")
                    print("          Event timing will not be marked for this component")
                    print("          Please consider marking the component via code component")
                    # remove unsupported response types
                    componentsForEyeLinkRespEventMessages.remove(thisComponent)
        
        # Open a draw list file (DLF) to which Data Viewer drawing information will be logged
        # The commands that will be written to this DLF file will enable
        # Data Viewer to reproduce the stimuli in its Trial View window
        sentDrawListMessage = False
        # create a folder for the current testing session in the "results" folder
        drawList_folder = os.path.join(results_folder, session_identifier,"graphics")
        if not os.path.exists(drawList_folder):
            os.makedirs(drawList_folder)
        # open a DRAW LIST file to save the frame timing info for the video, which will
        # help us to be able to see the video in Data Viewer's Trial View window
        # See the Data Viewer User Manual section:
        # "Procotol for EyeLink Data to Viewer Integration -> Simple Drawing Commands"
        dlf = 'TRIAL_%04d_ROUTINE_%02d.dlf' % (trial_index,routine_index)
        dlf_file = open(os.path.join(drawList_folder, dlf), 'w')
        
        # Open an Interest Area Set (IAS) file to which interest area information will be logged
        # Interest Areas will appear in Data Viewer and assist with analysis
        # See the Data Viewer User Manual section: 
        # "Procotol for EyeLink Data to Viewer Integration -> Interest Area Commands"
        sentIASFileMessage = False
        interestAreaSet_folder = os.path.join(results_folder, session_identifier,"aoi")
        if not os.path.exists(interestAreaSet_folder):
            os.makedirs(interestAreaSet_folder)
        # open the IAS file to save the interest area info for the stimuli
        ias = 'TRIAL_%04d_ROUTINE_%02d.ias' % (trial_index,routine_index)
        ias_file = open(os.path.join(interestAreaSet_folder, ias), 'w')
        # Update a routine index for EyeLink IAS/DLF file logging -- 
        # Each routine will have its own set of IAS/DLF files, as each will have its own  Mark Events component
        routine_index = routine_index + 1
        # Send a Data Viewer clear screen command to clear its Trial View window
        # to the window color
        el_tracker.sendMessage('!V CLEAR %d %d %d' % eyelink_color(win.color))
        # create a keyboard instance and reinitialize a kePressNameList, which
        # will store list of key names currently being pressed (to allow Ctrl-C abort)
        kb = keyboard.Keyboard()
        keyPressNameList = []
        eyelinkThisFrameCallOnFlipScheduled = False
        eyelinkLastFlipTime = 0.0
        routineTimer.reset()
        # store start times for TR1_image_display
        TR1_image_display.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        TR1_image_display.tStart = globalClock.getTime(format='float')
        TR1_image_display.status = STARTED
        thisExp.addData('TR1_image_display.started', TR1_image_display.tStart)
        TR1_image_display.maxDuration = None
        # keep track of which components have finished
        TR1_image_displayComponents = TR1_image_display.components
        for thisComponent in TR1_image_display.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "TR1_image_display" ---
        # if trial has changed, end Routine now
        if isinstance(free_view_loop, data.TrialHandler2) and thisFree_view_loop.thisN != free_view_loop.thisTrial.thisN:
            continueRoutine = False
        TR1_image_display.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *tr1_crosshair* updates
            
            # if tr1_crosshair is starting this frame...
            if tr1_crosshair.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                tr1_crosshair.frameNStart = frameN  # exact frame index
                tr1_crosshair.tStart = t  # local t and not account for scr refresh
                tr1_crosshair.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(tr1_crosshair, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'tr1_crosshair.started')
                # update status
                tr1_crosshair.status = STARTED
                tr1_crosshair.setAutoDraw(True)
            
            # if tr1_crosshair is active this frame...
            if tr1_crosshair.status == STARTED:
                # update params
                pass
            
            # if tr1_crosshair is stopping this frame...
            if tr1_crosshair.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > tr1_crosshair.tStartRefresh + fixDur-frameTolerance:
                    # keep track of stop time/frame for later
                    tr1_crosshair.tStop = t  # not accounting for scr refresh
                    tr1_crosshair.tStopRefresh = tThisFlipGlobal  # on global time
                    tr1_crosshair.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'tr1_crosshair.stopped')
                    # update status
                    tr1_crosshair.status = FINISHED
                    tr1_crosshair.setAutoDraw(False)
            
            # *tr1_image* updates
            
            # if tr1_image is starting this frame...
            if tr1_image.status == NOT_STARTED and tThisFlip >= fixDur+4-frameTolerance:
                # keep track of start time/frame for later
                tr1_image.frameNStart = frameN  # exact frame index
                tr1_image.tStart = t  # local t and not account for scr refresh
                tr1_image.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(tr1_image, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'tr1_image.started')
                # update status
                tr1_image.status = STARTED
                tr1_image.setAutoDraw(True)
            
            # if tr1_image is active this frame...
            if tr1_image.status == STARTED:
                # update params
                pass
            # This section of EyeLink MarkEvents component code checks whether to send (and sends/logs when appropriate)
            # event marking messages, log Data Viewer (DV) stimulus drawing info, log DV interest area info,
            # send DV Target Position Messages, and/or log DV video frame marking info
            if not eyelinkThisFrameCallOnFlipScheduled:
                # This method, created by the EyeLink MarkEvents component code will get called to handle
                # sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
                # sending DV Target Position Messages, and/or logging DV video frame marking info=information
                win.callOnFlip(eyelink_onFlip_MarkEvents,globalClock,win,scn_width,scn_height,allStimComponentsForEyeLinkMonitoring,\
                    componentsForEyeLinkStimEventMessages,\
                    componentsForEyeLinkStimDVDrawingMessages,dlf,dlf_file,\
                    componentsForEyeLinkInterestAreaMessages,ias,ias_file,interestAreaMargins)
                eyelinkThisFrameCallOnFlipScheduled = True
            
            # abort the current trial if the tracker is no longer recording
            error = el_tracker.isRecording()
            if error is not pylink.TRIAL_OK:
                el_tracker.sendMessage('tracker_disconnected')
                abort_trial(win,genv)
            
            # check keyboard events for experiment abort key combination
            keyPressList = kb.getKeys(keyList = ['lctrl','rctrl','c'], waitRelease = False, clear = False)
            for keyPress in keyPressList:
                keyPressName = keyPress.name
                if keyPressName not in keyPressNameList:
                    keyPressNameList.append(keyPress.name)
            if ('lctrl' in keyPressNameList or 'rctrl' in keyPressNameList) and 'c' in keyPressNameList:
                el_tracker.sendMessage('terminated_by_user')
                terminate_task(win,genv,edf_file,session_folder,session_identifier)
            #check for key releases
            keyReleaseList = kb.getKeys(keyList = ['lctrl','rctrl','c'], waitRelease = True, clear = False)
            for keyRelease in keyReleaseList:
                keyReleaseName = keyRelease.name
                if keyReleaseName in keyPressNameList:
                    keyPressNameList.remove(keyReleaseName)
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                TR1_image_display.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in TR1_image_display.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "TR1_image_display" ---
        for thisComponent in TR1_image_display.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for TR1_image_display
        TR1_image_display.tStop = globalClock.getTime(format='float')
        TR1_image_display.tStopRefresh = tThisFlipGlobal
        thisExp.addData('TR1_image_display.stopped', TR1_image_display.tStop)
        
        # This section of EyeLink MarkEvents component code does some event cleanup at the end of the routine
        # Go through all stimulus components that need to be checked for event marking,
        #  to see if the trial ended before PsychoPy reported OFFSET detection to mark their offset from trial end
        for thisComponent in componentsForEyeLinkStimEventMessages:
            if thisComponent.elOnsetDetected and not thisComponent.elOffsetDetected:
                # Check if the component had onset but the trial ended before offset
                el_tracker.sendMessage('%s_OFFSET' % (thisComponent.name))
        # Go through all response components whose occurence/data
        # need to be logged to the EDF and marks their occurence with a message (using an offset calculation that backstam
        for thisComponent in componentsForEyeLinkRespEventMessages:
            if thisComponent.componentType == "Keyboard" or thisComponent.componentType == "OtherRespWithRT":
                if not isinstance(thisComponent.rt,list):
                    offsetValue = int(round((globalClock.getTime() - \
                        (thisComponent.tStartRefresh + thisComponent.rt))*1000))
                    el_tracker.sendMessage('%i %s_EVENT' % (offsetValue,thisComponent.componentType,))
                    # if sending many messages in a row, add a 1 msec pause between after
                    # every 5 messages or so
                if isinstance(thisComponent.rt,list) and len(thisComponent.rt) > 0:
                    for i in range(len(thisComponent.rt)):
                        offsetValue = int(round((globalClock.getTime() - \
                            (thisComponent.tStartRefresh + thisComponent.rt[i]))*1000))
                        el_tracker.sendMessage('%i %s_EVENT_%i' % (offsetValue,thisComponent.componentType,i+1))
                        if i % 4 == 0:
                            # if sending many messages in a row, add a 1 msec pause between after 
                            # every 5 messages or so
                            time.sleep(0.001)
                el_tracker.sendMessage('!V TRIAL_VAR %s.rt(s) %s' % (thisComponent.componentType,thisComponent.rt))
                if "corr" in dir(thisComponent):
                    el_tracker.sendMessage('!V TRIAL_VAR %s.corr %s' % (thisComponent.componentType,thisComponent.corr))
                if "keys" in dir(thisComponent):
                    el_tracker.sendMessage('!V TRIAL_VAR %s.keys %s' % (thisComponent.componentType,thisComponent.keys))
            elif thisComponent.componentType == "Mouse" or thisComponent.componentType == "OtherRespWithTime":
                if not isinstance(thisComponent.time,list):
                    offsetValue = int(round((globalClock.getTime() - \
                        (thisComponent.tStartRefresh + thisComponent.time))*1000))
                    el_tracker.sendMessage('%i %s_EVENT' % (thisComponent.componentType,offsetValue))
                    # if sending many messages in a row, add a 1 msec pause between after 
                    # every 5 messages or so
                    time.sleep(0.0005)
                if isinstance(thisComponent.time,list) and len(thisComponent.time) > 0:
                    for i in range(len(thisComponent.time)):
                        offsetValue = int(round((globalClock.getTime() - \
                            (thisComponent.tStartRefresh + thisComponent.time[i]))*1000))
                        el_tracker.sendMessage('%i %s_EVENT_%i' % (offsetValue,thisComponent.componentType,i+1))
                        if i % 4 == 0:
                            # if sending many messages in a row, add a 1 msec pause between after 
                            # every 5 messages or so
                            time.sleep(0.001)
                el_tracker.sendMessage('!V TRIAL_VAR %s.time(s) %s' % (thisComponent.componentType,thisComponent.time))
            time.sleep(0.001)
        
        # log any remaining interest area commands to the IAS file for stimuli that 
        # were still being presented when the routine ended
        for thisComponent in componentsForEyeLinkInterestAreaMessages:
            if not thisComponent.elOffsetDetected and thisComponent.tStartRefresh is not None:
                ias_file.write('%i %i IAREA %s %i %i %i %i %i %s\n' % \
                    (int(round((zeroTimeIAS - thisComponent.iaInstanceStartTime)*1000)),
                    int(round((zeroTimeIAS - globalClock.getTime())*1000 - 1)),"RECTANGLE",thisComponent.iaIndex,
                    thisComponent.elPos[0]-(thisComponent.elSize[0]/2+interestAreaMargins),
                    thisComponent.elPos[1]-(thisComponent.elSize[1]/2+interestAreaMargins),
                    thisComponent.elPos[0]+(thisComponent.elSize[0]/2+interestAreaMargins),
                    thisComponent.elPos[1]+(thisComponent.elSize[1]/2+interestAreaMargins),thisComponent.name))
        # Close the interest area set file and draw list file for the trial
        ias_file.close()
        # close the drawlist file (which is used in Data Viewer stimulus presntation re-creation)
        dlf_file.close()
        
        # the Routine "TR1_image_display" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        
        # --- Prepare to start Routine "TR1_eyelink_stop" ---
        # create an object to store info about Routine TR1_eyelink_stop
        TR1_eyelink_stop = data.Routine(
            name='TR1_eyelink_stop',
            components=[StopRecord],
        )
        TR1_eyelink_stop.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for TR1_eyelink_stop
        TR1_eyelink_stop.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        TR1_eyelink_stop.tStart = globalClock.getTime(format='float')
        TR1_eyelink_stop.status = STARTED
        thisExp.addData('TR1_eyelink_stop.started', TR1_eyelink_stop.tStart)
        TR1_eyelink_stop.maxDuration = None
        # keep track of which components have finished
        TR1_eyelink_stopComponents = TR1_eyelink_stop.components
        for thisComponent in TR1_eyelink_stop.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "TR1_eyelink_stop" ---
        # if trial has changed, end Routine now
        if isinstance(free_view_loop, data.TrialHandler2) and thisFree_view_loop.thisN != free_view_loop.thisTrial.thisN:
            continueRoutine = False
        TR1_eyelink_stop.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 0.001:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                TR1_eyelink_stop.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in TR1_eyelink_stop.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "TR1_eyelink_stop" ---
        for thisComponent in TR1_eyelink_stop.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for TR1_eyelink_stop
        TR1_eyelink_stop.tStop = globalClock.getTime(format='float')
        TR1_eyelink_stop.tStopRefresh = tThisFlipGlobal
        thisExp.addData('TR1_eyelink_stop.stopped', TR1_eyelink_stop.tStop)
        # This section of EyeLink StopRecord component code stops recording, sends a trial end (TRIAL_RESULT)
        # message to the EDF, and updates the trial_index variable 
        el_tracker.stopRecording()
        
        # send a 'TRIAL_RESULT' message to mark the end of trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        el_tracker.sendMessage('TRIAL_RESULT %d' % 0)
        
        # update the trial counter for the next trial
        trial_index = trial_index + 1
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if TR1_eyelink_stop.maxDurationReached:
            routineTimer.addTime(-TR1_eyelink_stop.maxDuration)
        elif TR1_eyelink_stop.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-0.001000)
        
        # --- Prepare to start Routine "inter_trial_interval" ---
        # create an object to store info about Routine inter_trial_interval
        inter_trial_interval = data.Routine(
            name='inter_trial_interval',
            components=[blank_iti],
        )
        inter_trial_interval.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for inter_trial_interval
        inter_trial_interval.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        inter_trial_interval.tStart = globalClock.getTime(format='float')
        inter_trial_interval.status = STARTED
        thisExp.addData('inter_trial_interval.started', inter_trial_interval.tStart)
        inter_trial_interval.maxDuration = None
        # keep track of which components have finished
        inter_trial_intervalComponents = inter_trial_interval.components
        for thisComponent in inter_trial_interval.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "inter_trial_interval" ---
        # if trial has changed, end Routine now
        if isinstance(free_view_loop, data.TrialHandler2) and thisFree_view_loop.thisN != free_view_loop.thisTrial.thisN:
            continueRoutine = False
        inter_trial_interval.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *blank_iti* updates
            
            # if blank_iti is starting this frame...
            if blank_iti.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                blank_iti.frameNStart = frameN  # exact frame index
                blank_iti.tStart = t  # local t and not account for scr refresh
                blank_iti.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(blank_iti, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'blank_iti.started')
                # update status
                blank_iti.status = STARTED
                blank_iti.setAutoDraw(True)
            
            # if blank_iti is active this frame...
            if blank_iti.status == STARTED:
                # update params
                pass
            
            # if blank_iti is stopping this frame...
            if blank_iti.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > blank_iti.tStartRefresh + iti-frameTolerance:
                    # keep track of stop time/frame for later
                    blank_iti.tStop = t  # not accounting for scr refresh
                    blank_iti.tStopRefresh = tThisFlipGlobal  # on global time
                    blank_iti.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'blank_iti.stopped')
                    # update status
                    blank_iti.status = FINISHED
                    blank_iti.setAutoDraw(False)
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                inter_trial_interval.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in inter_trial_interval.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "inter_trial_interval" ---
        for thisComponent in inter_trial_interval.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for inter_trial_interval
        inter_trial_interval.tStop = globalClock.getTime(format='float')
        inter_trial_interval.tStopRefresh = tThisFlipGlobal
        thisExp.addData('inter_trial_interval.stopped', inter_trial_interval.tStop)
        # the Routine "inter_trial_interval" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
    # completed 1.0 repeats of 'free_view_loop'
    
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    # get names of stimulus parameters
    if free_view_loop.trialList in ([], [None], None):
        params = []
    else:
        params = free_view_loop.trialList[0].keys()
    # save data for this loop
    free_view_loop.saveAsExcel(filename + '.xlsx', sheetName='free_view_loop',
        stimOut=params,
        dataOut=['n','all_mean','all_std', 'all_raw'])
    free_view_loop.saveAsText(filename + 'free_view_loop.csv', delim=',',
        stimOut=params,
        dataOut=['n','all_mean','all_std', 'all_raw'])
    
    # --- Prepare to start Routine "Break" ---
    # create an object to store info about Routine Break
    Break = data.Routine(
        name='Break',
        components=[break_text, key_resp_break],
    )
    Break.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for key_resp_break
    key_resp_break.keys = []
    key_resp_break.rt = []
    _key_resp_break_allKeys = []
    # store start times for Break
    Break.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Break.tStart = globalClock.getTime(format='float')
    Break.status = STARTED
    thisExp.addData('Break.started', Break.tStart)
    Break.maxDuration = None
    # keep track of which components have finished
    BreakComponents = Break.components
    for thisComponent in Break.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "Break" ---
    Break.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *break_text* updates
        
        # if break_text is starting this frame...
        if break_text.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            break_text.frameNStart = frameN  # exact frame index
            break_text.tStart = t  # local t and not account for scr refresh
            break_text.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(break_text, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'break_text.started')
            # update status
            break_text.status = STARTED
            break_text.setAutoDraw(True)
        
        # if break_text is active this frame...
        if break_text.status == STARTED:
            # update params
            pass
        
        # *key_resp_break* updates
        waitOnFlip = False
        
        # if key_resp_break is starting this frame...
        if key_resp_break.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            key_resp_break.frameNStart = frameN  # exact frame index
            key_resp_break.tStart = t  # local t and not account for scr refresh
            key_resp_break.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(key_resp_break, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'key_resp_break.started')
            # update status
            key_resp_break.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(key_resp_break.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(key_resp_break.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if key_resp_break.status == STARTED and not waitOnFlip:
            theseKeys = key_resp_break.getKeys(keyList=["space"], ignoreKeys=None, waitRelease=False)
            _key_resp_break_allKeys.extend(theseKeys)
            if len(_key_resp_break_allKeys):
                key_resp_break.keys = _key_resp_break_allKeys[-1].name  # just the last key pressed
                key_resp_break.rt = _key_resp_break_allKeys[-1].rt
                key_resp_break.duration = _key_resp_break_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            Break.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in Break.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "Break" ---
    for thisComponent in Break.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Break
    Break.tStop = globalClock.getTime(format='float')
    Break.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Break.stopped', Break.tStop)
    # check responses
    if key_resp_break.keys in ['', [], None]:  # No response was made
        key_resp_break.keys = None
    thisExp.addData('key_resp_break.keys',key_resp_break.keys)
    if key_resp_break.keys != None:  # we had a response
        thisExp.addData('key_resp_break.rt', key_resp_break.rt)
        thisExp.addData('key_resp_break.duration', key_resp_break.duration)
    thisExp.nextEntry()
    # the Routine "Break" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "Trial_calib" ---
    # create an object to store info about Routine Trial_calib
    Trial_calib = data.Routine(
        name='Trial_calib',
        components=[CameraSetup_3],
    )
    Trial_calib.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # store start times for Trial_calib
    Trial_calib.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Trial_calib.tStart = globalClock.getTime(format='float')
    Trial_calib.status = STARTED
    thisExp.addData('Trial_calib.started', Trial_calib.tStart)
    Trial_calib.maxDuration = None
    # keep track of which components have finished
    Trial_calibComponents = Trial_calib.components
    for thisComponent in Trial_calib.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "Trial_calib" ---
    Trial_calib.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 0.001:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            Trial_calib.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in Trial_calib.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "Trial_calib" ---
    for thisComponent in Trial_calib.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Trial_calib
    Trial_calib.tStop = globalClock.getTime(format='float')
    Trial_calib.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Trial_calib.stopped', Trial_calib.tStop)
    # This section of EyeLink CameraSetup_3 component code configures some
    # graphics options for calibration, and then performs a camera setup
    # so that you can set up the eye tracker and calibrate/validate the participant
    # graphics options for calibration, and then performs a camera setup
    # so that you can set up the eye tracker and calibrate/validate the participant
    
    # Set background and foreground colors for the calibration target
    # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
    background_color = (1, 1, 1)
    foreground_color = (0,0,0)
    genv.setCalibrationColors(foreground_color, background_color)
    
    # Set up the calibration/validation target
    #
    # The target could be a "circle" (default), a "picture", a "movie" clip,
    # or a rotating "spiral". To configure the type of drift check target, set
    # genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
    genv.setTargetType('picture')
    #
    # Use a picture as the drift check target
    # Use genv.setPictureTarget() to set a "movie" target
    genv.setPictureTarget(os.path.normpath('images/fixTarget2.png'))
    
    # Beeps to play during calibration, validation and drift correction
    # parameters: target, good, error
    #     target -- sound to play when target moves
    #     good -- sound to play on successful operation
    #     error -- sound to play on failure or interruption
    # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
    genv.setCalibrationSounds('', '', '')
    
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    el_tracker.sendCommand("calibration_type = " 'HV9')
    #clear the screen before we begin Camera Setup mode
    clear_screen(win,genv)
    
    
    # Go into Camera Setup mode so that participant setup/EyeLink calibration/validation can be performed
    # skip this step if running the script in Dummy Mode
    if not dummy_mode:
        try:
            el_tracker.doTrackerSetup()
        except RuntimeError as err:
            print('ERROR:', err)
            el_tracker.exitCalibration()
        else:
            win.mouseVisible = False
    # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
    if Trial_calib.maxDurationReached:
        routineTimer.addTime(-Trial_calib.maxDuration)
    elif Trial_calib.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-0.001000)
    thisExp.nextEntry()
    
    # --- Prepare to start Routine "S1_instruct" ---
    # create an object to store info about Routine S1_instruct
    S1_instruct = data.Routine(
        name='S1_instruct',
        components=[s1_textbox_instruct, s1_key_resp_instruct],
    )
    S1_instruct.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    s1_textbox_instruct.reset()
    # create starting attributes for s1_key_resp_instruct
    s1_key_resp_instruct.keys = []
    s1_key_resp_instruct.rt = []
    _s1_key_resp_instruct_allKeys = []
    # store start times for S1_instruct
    S1_instruct.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    S1_instruct.tStart = globalClock.getTime(format='float')
    S1_instruct.status = STARTED
    thisExp.addData('S1_instruct.started', S1_instruct.tStart)
    S1_instruct.maxDuration = None
    # keep track of which components have finished
    S1_instructComponents = S1_instruct.components
    for thisComponent in S1_instruct.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "S1_instruct" ---
    S1_instruct.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *s1_textbox_instruct* updates
        
        # if s1_textbox_instruct is starting this frame...
        if s1_textbox_instruct.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            s1_textbox_instruct.frameNStart = frameN  # exact frame index
            s1_textbox_instruct.tStart = t  # local t and not account for scr refresh
            s1_textbox_instruct.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(s1_textbox_instruct, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 's1_textbox_instruct.started')
            # update status
            s1_textbox_instruct.status = STARTED
            s1_textbox_instruct.setAutoDraw(True)
        
        # if s1_textbox_instruct is active this frame...
        if s1_textbox_instruct.status == STARTED:
            # update params
            pass
        
        # *s1_key_resp_instruct* updates
        waitOnFlip = False
        
        # if s1_key_resp_instruct is starting this frame...
        if s1_key_resp_instruct.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            s1_key_resp_instruct.frameNStart = frameN  # exact frame index
            s1_key_resp_instruct.tStart = t  # local t and not account for scr refresh
            s1_key_resp_instruct.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(s1_key_resp_instruct, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 's1_key_resp_instruct.started')
            # update status
            s1_key_resp_instruct.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(s1_key_resp_instruct.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(s1_key_resp_instruct.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if s1_key_resp_instruct.status == STARTED and not waitOnFlip:
            theseKeys = s1_key_resp_instruct.getKeys(keyList=None, ignoreKeys=None, waitRelease=False)
            _s1_key_resp_instruct_allKeys.extend(theseKeys)
            if len(_s1_key_resp_instruct_allKeys):
                s1_key_resp_instruct.keys = _s1_key_resp_instruct_allKeys[-1].name  # just the last key pressed
                s1_key_resp_instruct.rt = _s1_key_resp_instruct_allKeys[-1].rt
                s1_key_resp_instruct.duration = _s1_key_resp_instruct_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            S1_instruct.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in S1_instruct.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "S1_instruct" ---
    for thisComponent in S1_instruct.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for S1_instruct
    S1_instruct.tStop = globalClock.getTime(format='float')
    S1_instruct.tStopRefresh = tThisFlipGlobal
    thisExp.addData('S1_instruct.stopped', S1_instruct.tStop)
    # check responses
    if s1_key_resp_instruct.keys in ['', [], None]:  # No response was made
        s1_key_resp_instruct.keys = None
    thisExp.addData('s1_key_resp_instruct.keys',s1_key_resp_instruct.keys)
    if s1_key_resp_instruct.keys != None:  # we had a response
        thisExp.addData('s1_key_resp_instruct.rt', s1_key_resp_instruct.rt)
        thisExp.addData('s1_key_resp_instruct.duration', s1_key_resp_instruct.duration)
    thisExp.nextEntry()
    # the Routine "S1_instruct" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # set up handler to look after randomisation of conditions etc
    experiment_loop = data.TrialHandler2(
        name='experiment_loop',
        nReps=1.0, 
        method='fullRandom', 
        extraInfo=expInfo, 
        originPath=-1, 
        trialList=data.importConditions(cond_file_far_near_test), 
        seed=None, 
    )
    thisExp.addLoop(experiment_loop)  # add the loop to the experiment
    thisExperiment_loop = experiment_loop.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisExperiment_loop.rgb)
    if thisExperiment_loop != None:
        for paramName in thisExperiment_loop:
            globals()[paramName] = thisExperiment_loop[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    
    for thisExperiment_loop in experiment_loop:
        currentLoop = experiment_loop
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisExperiment_loop.rgb)
        if thisExperiment_loop != None:
            for paramName in thisExperiment_loop:
                globals()[paramName] = thisExperiment_loop[paramName]
        
        # --- Prepare to start Routine "S1_Break" ---
        # create an object to store info about Routine S1_Break
        S1_Break = data.Routine(
            name='S1_Break',
            components=[textbox_break_2, timer_clock_trial_2, key_resp_trial_break_2],
        )
        S1_Break.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from break_code_2
        if ((far_near_train_loop.thisN+1) % drift_interval != 0):
          do_drift = False
        else:
          do_drift = True
        
        trial_break_message = 'Time for a break. \n You have completed %s of %s trials! \n You can press any button when ready.'%(far_near_test_loop.thisN, len(far_near_test_loop.trialList)*far_near_test_loop.nReps)
        if ((far_near_test_loop.thisN) % s1_break != 0) or (far_near_test_loop.thisN ==0):
            continueRoutine = False
        
        textbox_break_2.reset()
        textbox_break_2.setText(trial_break_message)
        # create starting attributes for key_resp_trial_break_2
        key_resp_trial_break_2.keys = []
        key_resp_trial_break_2.rt = []
        _key_resp_trial_break_2_allKeys = []
        # store start times for S1_Break
        S1_Break.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        S1_Break.tStart = globalClock.getTime(format='float')
        S1_Break.status = STARTED
        thisExp.addData('S1_Break.started', S1_Break.tStart)
        S1_Break.maxDuration = None
        # keep track of which components have finished
        S1_BreakComponents = S1_Break.components
        for thisComponent in S1_Break.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "S1_Break" ---
        # if trial has changed, end Routine now
        if isinstance(experiment_loop, data.TrialHandler2) and thisExperiment_loop.thisN != experiment_loop.thisTrial.thisN:
            continueRoutine = False
        S1_Break.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *textbox_break_2* updates
            
            # if textbox_break_2 is starting this frame...
            if textbox_break_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                textbox_break_2.frameNStart = frameN  # exact frame index
                textbox_break_2.tStart = t  # local t and not account for scr refresh
                textbox_break_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(textbox_break_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'textbox_break_2.started')
                # update status
                textbox_break_2.status = STARTED
                textbox_break_2.setAutoDraw(True)
            
            # if textbox_break_2 is active this frame...
            if textbox_break_2.status == STARTED:
                # update params
                pass
            
            # *timer_clock_trial_2* updates
            
            # if timer_clock_trial_2 is starting this frame...
            if timer_clock_trial_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                timer_clock_trial_2.frameNStart = frameN  # exact frame index
                timer_clock_trial_2.tStart = t  # local t and not account for scr refresh
                timer_clock_trial_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(timer_clock_trial_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'timer_clock_trial_2.started')
                # update status
                timer_clock_trial_2.status = STARTED
                timer_clock_trial_2.setAutoDraw(True)
            
            # if timer_clock_trial_2 is active this frame...
            if timer_clock_trial_2.status == STARTED:
                # update params
                timer_clock_trial_2.setText(round(30.0 - t, ndigits = 1), log=False)
            
            # *key_resp_trial_break_2* updates
            waitOnFlip = False
            
            # if key_resp_trial_break_2 is starting this frame...
            if key_resp_trial_break_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                key_resp_trial_break_2.frameNStart = frameN  # exact frame index
                key_resp_trial_break_2.tStart = t  # local t and not account for scr refresh
                key_resp_trial_break_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(key_resp_trial_break_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'key_resp_trial_break_2.started')
                # update status
                key_resp_trial_break_2.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(key_resp_trial_break_2.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(key_resp_trial_break_2.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if key_resp_trial_break_2.status == STARTED and not waitOnFlip:
                theseKeys = key_resp_trial_break_2.getKeys(keyList=['space','3','4'], ignoreKeys=None, waitRelease=False)
                _key_resp_trial_break_2_allKeys.extend(theseKeys)
                if len(_key_resp_trial_break_2_allKeys):
                    key_resp_trial_break_2.keys = _key_resp_trial_break_2_allKeys[-1].name  # just the last key pressed
                    key_resp_trial_break_2.rt = _key_resp_trial_break_2_allKeys[-1].rt
                    key_resp_trial_break_2.duration = _key_resp_trial_break_2_allKeys[-1].duration
                    # a response ends the routine
                    continueRoutine = False
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                S1_Break.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in S1_Break.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "S1_Break" ---
        for thisComponent in S1_Break.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for S1_Break
        S1_Break.tStop = globalClock.getTime(format='float')
        S1_Break.tStopRefresh = tThisFlipGlobal
        thisExp.addData('S1_Break.stopped', S1_Break.tStop)
        # check responses
        if key_resp_trial_break_2.keys in ['', [], None]:  # No response was made
            key_resp_trial_break_2.keys = None
        experiment_loop.addData('key_resp_trial_break_2.keys',key_resp_trial_break_2.keys)
        if key_resp_trial_break_2.keys != None:  # we had a response
            experiment_loop.addData('key_resp_trial_break_2.rt', key_resp_trial_break_2.rt)
            experiment_loop.addData('key_resp_trial_break_2.duration', key_resp_trial_break_2.duration)
        # the Routine "S1_Break" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        
        # --- Prepare to start Routine "S1_eyelink_start" ---
        # create an object to store info about Routine S1_eyelink_start
        S1_eyelink_start = data.Routine(
            name='S1_eyelink_start',
            components=[HostDrawing_2, DriftCheck_2, StartRecord_2],
        )
        S1_eyelink_start.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for S1_eyelink_start
        S1_eyelink_start.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        S1_eyelink_start.tStart = globalClock.getTime(format='float')
        S1_eyelink_start.status = STARTED
        thisExp.addData('S1_eyelink_start.started', S1_eyelink_start.tStart)
        S1_eyelink_start.maxDuration = None
        # keep track of which components have finished
        S1_eyelink_startComponents = S1_eyelink_start.components
        for thisComponent in S1_eyelink_start.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "S1_eyelink_start" ---
        # if trial has changed, end Routine now
        if isinstance(experiment_loop, data.TrialHandler2) and thisExperiment_loop.thisN != experiment_loop.thisTrial.thisN:
            continueRoutine = False
        S1_eyelink_start.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 0.001:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                S1_eyelink_start.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in S1_eyelink_start.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "S1_eyelink_start" ---
        for thisComponent in S1_eyelink_start.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for S1_eyelink_start
        S1_eyelink_start.tStop = globalClock.getTime(format='float')
        S1_eyelink_start.tStopRefresh = tThisFlipGlobal
        thisExp.addData('S1_eyelink_start.stopped', S1_eyelink_start.tStop)
        # This section of EyeLink HostDrawing_2 component code provides options for sending images/shapes
        # representing stimuli to the Host PC backdrop for real-time gaze monitoring
        
        # get a reference to the currently active EyeLink connection
        el_tracker = pylink.getEYELINK()
        # put the tracker in the offline mode first
        el_tracker.setOfflineMode()
        # clear the host screen before we draw the backdrop
        el_tracker.sendCommand('clear_screen 0')
        # imagesAndComponentsStringList value = ['file,s1_image']
        # Send image components to the Host PC backdrop to serve as landmarks during recording
        # The method bitmapBackdrop() requires a step of converting the
        # image pixels into a recognizable format by the Host PC.
        # pixels = [line1, ...lineH], line = [pix1,...pixW], pix=(R,G,B)
        # the bitmapBackdrop() command takes time to return, not recommended
        # for tasks where the ITI matters, e.g., in an event-related fMRI task
        # parameters: width, height, pixel, crop_x, crop_y,
        #             crop_width, crop_height, x, y on the Host, drawing options
        imagesAndComponentsListForHostBackdrop = [[file, s1_image]]
        # get the array of blank pixels where each pixel corresponds to win.color
        pixels = blankHostPixels[::]
        # go through each image and replace the pixels in the blank array with the image pixels
        for thisImage in imagesAndComponentsListForHostBackdrop:
            thisImageFile = thisImage[0]
            thisImageComponent = thisImage[1]
            thisImageComponent.setImage(thisImageFile)
            if "Image" in str(thisImageComponent.__class__):
                # Use the code commented below to convert the image and send the backdrop
                im = Image.open(script_path + "/" + thisImageFile)
                thisImageComponent.elPos = eyelink_pos(thisImageComponent.pos,[scn_width,scn_height])
                thisImageComponent.elSize = eyelink_size(thisImageComponent.size,[scn_width,scn_height])
                imWidth = int(round(thisImageComponent.elSize[0]))
                imHeight = int(round(thisImageComponent.elSize[1]))
                imLeft = int(round(thisImageComponent.elPos[0]-thisImageComponent.elSize[0]/2))
                imTop = int(round(thisImageComponent.elPos[1]-thisImageComponent.elSize[1]/2))
                im = im.resize((imWidth,imHeight))
                # Access the pixel data of the image
                img_pixels = list(im.getdata())
                # Check to see if the image goes off the screen
                # If so, adjust the coordinates appropriately
                if imLeft < 0:
                    imTransferLeft = 0
                else:
                    imTransferLeft = imLeft
                if imTop < 0:
                    imTransferTop = 0
                else:
                    imTransferTop = imTop
                if imLeft + imWidth > scn_width:
                    imTransferRight = scn_width
                else:
                    imTransferRight = imLeft+imWidth
                if imTop + imHeight > scn_height:
                    imTransferBottom = scn_height
                else:
                    imTransferBottom = imTop+imHeight    
                imTransferImageLineStartX = imTransferLeft-imLeft
                imTransferImageLineEndX = imTransferRight-imTransferLeft+imTransferImageLineStartX
                imTransferImageLineStartY = imTransferTop-imTop
                for y in range(imTransferBottom-imTransferTop):
                    pixels[imTransferTop+y][imTransferLeft:imTransferRight] = \
                        img_pixels[(imTransferImageLineStartY + y)*imWidth+imTransferImageLineStartX:\
                        (imTransferImageLineStartY + y)*imWidth + imTransferImageLineEndX]
            else:
                print("WARNING: Image Transfer Not Supported For non-Image Component %s)" % str(thisComponent.__class__))
        # transfer the full-screen pixel array to the Host PC
        el_tracker.bitmapBackdrop(scn_width,scn_height, pixels,\
            0, 0, scn_width, scn_height, 0, 0, pylink.BX_MAXCONTRAST)
        # Draw rectangles along the edges of components to serve as landmarks on the Host PC backdrop during recording
        # For a list of supported draw commands, see the "COMMANDS.INI" file on the Host PC
        componentDrawListForHostBackdrop = [s1_crosshair]
        for thisComponent in componentDrawListForHostBackdrop:
                thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                drawColor = 4
                drawCommand = "draw_box = %i %i %i %i %i" % (thisComponent.elPos[0] - thisComponent.elSize[0]/2,
                    thisComponent.elPos[1] - thisComponent.elSize[1]/2, thisComponent.elPos[0] + thisComponent.elSize[0]/2,
                    thisComponent.elPos[1] + thisComponent.elSize[1]/2, drawColor)
                el_tracker.sendCommand(drawCommand)
        # record_status_message -- send a messgae string to the Host PC that will be present during recording
        el_tracker.sendCommand("record_status_message '%s'" % ("Trial %s" % trial_index))
        # This section of EyeLink DriftCheck_2 component code configures some
        # graphics options for drift check, and then performs the drift check
        # Set background and foreground colors for the drift check target
        # in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
        background_color = (1,1,1)
        foreground_color = (0,0,0)
        genv.setCalibrationColors(foreground_color, background_color)
        # Set up the drift check target
        # The target could be a "circle" (default), a "picture", a "movie" clip,
        # or a rotating "spiral". To configure the type of drift check target, set
        # genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
        genv.setTargetType('picture')
        # Use a picture as the drift check target
        # Use genv.setPictureTarget() to set a "movie" target
        genv.setPictureTarget(os.path.normpath('images/fixTarget2.png'))
        # Beeps to play during calibration, validation and drift correction
        # parameters: target, good, error
        #     target -- sound to play when target moves
        #     good -- sound to play on successful operation
        #     error -- sound to play on failure or interruption
        # Each parameter could be ''--default sound, 'off'--no sound, or a wav file
        genv.setCalibrationSounds('', '', '')
        
        # drift check
        # the doDriftCorrect() function requires target position in integers
        # the last two arguments:
        # draw_target (1-default, 0-draw the target then call doDriftCorrect)
        # allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
        
        # Skip drift-check if running the script in Dummy Mode
        while not dummy_mode:
            # terminate the task if no longer connected to the tracker or
            # user pressed Ctrl-C to terminate the task
            if (not el_tracker.isConnected()) or el_tracker.breakPressed():
                terminate_task(win,genv,edf_file,session_folder,session_identifier)
            # drift-check and re-do camera setup if ESCAPE is pressed
            dcX,dcY = eyelink_pos([0,0],[scn_width,scn_height])
            try:
                error = el_tracker.doDriftCorrect(int(round(dcX)),int(round(dcY)),1,1)
                # break following a success drift-check
                if error is not pylink.ESC_KEY:
                    break
            except:
                pass
        # This section of EyeLink StartRecord_2 component code starts eye tracker recording,
        # sends a trial start (i.e., TRIALID) message to the EDF, 
        # and logs which eye is tracked
        
        # get a reference to the currently active EyeLink connection
        el_tracker = pylink.getEYELINK()
        # Send a "TRIALID" message to mark the start of a trial, see the following Data Viewer User Manual:
        # "Protocol for EyeLink Data to Viewer Integration -> Defining the Start and End of a Trial"
        el_tracker.sendMessage('TRIALID %d' % trial_index)
        # Log the trial index at the start of recording in case there will be multiple trials within one recording
        trialIDAtRecordingStart = int(trial_index)
        # Log the routine index at the start of recording in case there will be multiple routines within one recording
        routine_index = 1
        # put tracker in idle/offline mode before recording
        el_tracker.setOfflineMode()
        # Start recording, logging all samples/events to the EDF and making all data available over the link
        # arguments: sample_to_file, events_to_file, sample_over_link, events_over_link (1-yes, 0-no)
        try:
            el_tracker.startRecording(1, 1, 1, 1)
        except RuntimeError as error:
            print("ERROR:", error)
            abort_trial(genv)
        # Allocate some time for the tracker to cache some samples before allowing
        # trial stimulus presentation to proceed
        pylink.pumpDelay(100)
        # determine which eye(s) is/are available
        # 0-left, 1-right, 2-binocular
        eye_used = el_tracker.eyeAvailable()
        if eye_used == 1:
            el_tracker.sendMessage("EYE_USED 1 RIGHT")
        elif eye_used == 0 or eye_used == 2:
            el_tracker.sendMessage("EYE_USED 0 LEFT")
            eye_used = 0
        else:
            print("ERROR: Could not get eye information!")
        #routineForceEnded = True
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if S1_eyelink_start.maxDurationReached:
            routineTimer.addTime(-S1_eyelink_start.maxDuration)
        elif S1_eyelink_start.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-0.001000)
        
        # --- Prepare to start Routine "S1_image_display" ---
        # create an object to store info about Routine S1_image_display
        S1_image_display = data.Routine(
            name='S1_image_display',
            components=[s1_crosshair, s1_image, movie, MarkEvents_2],
        )
        S1_image_display.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from code_2
        # Fixation cross duration for this trial
        fixDur = np.random.uniform(fixDurMin, fixDurMax) # random between minimum and maximum
        thisExp.addData('fixation_duration',fixDur)
        if str(near_far) == '0':
            correct_keys = correct_near_button
        else:
            correct_keys = correct_far_button
        s1_image.setImage(image)
        movie.setMovie(video)
        # This section of EyeLink MarkEvents_2 component code initializes some variables that will help with
        # sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
        # sending DV Target Position Messages, and/or logging DV video frame marking info
        # information
        
        
        # log trial variables' values to the EDF data file, for details, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        trialConditionVariablesForEyeLinkLogging = [file,near_far,real_near_far_label,relation_correct,]
        trialConditionVariableNamesForEyeLinkLogging = ['file', 'near_far', 'real_near_far_label', 'relation_correct', '']
        for i in range(len(trialConditionVariablesForEyeLinkLogging)):
            el_tracker.sendMessage('!V TRIAL_VAR %s %s'% (trialConditionVariableNamesForEyeLinkLogging[i],trialConditionVariablesForEyeLinkLogging[i]))
            #add a brief pause after every 5 messages or so to make sure no messages are missed
            if i % 5 == 0:
                time.sleep(0.001)
        
        # list of all stimulus components whose onset/offset will be marked with messages
        componentsForEyeLinkStimEventMessages = [s1_crosshair,s1_image]
        # list of all stimulus components for which Data Viewer draw commands will be sent
        componentsForEyeLinkStimDVDrawingMessages = [s1_crosshair,s1_image]
        # list of all stimulus components which will have interest areas automatically created for them
        componentsForEyeLinkInterestAreaMessages = [s1_crosshair]
        # create list of all components to be monitored for EyeLink Marking/Messaging
        allStimComponentsForEyeLinkMonitoring = componentsForEyeLinkStimEventMessages + componentsForEyeLinkStimDVDrawingMessages + componentsForEyeLinkInterestAreaMessages# make sure each component is only in the list once
        allStimComponentsForEyeLinkMonitoring = [*set(allStimComponentsForEyeLinkMonitoring)]
        # list of all movie components whose individual frame onsets need to be marked
        componentsForEyeLinkMovieFrameMarking = []
        # list of all response components whose onsets need to be marked and values
        # need to be logged
        componentsForEyeLinkRespEventMessages = [s1_key_resp]
        
        # Initialize stimulus components whose occurence needs to be monitored for event
        # marking, Data Viewer integration, and/or interest area messaging
        # to the EDF (provided they are supported stimulus types)
        for thisComponent in allStimComponentsForEyeLinkMonitoring:
            componentClassString = str(thisComponent.__class__)
            supportedStimType = False
            for stimType in ["Aperture","Text","Dot","Shape","Rect","Grating","Image","MovieStim3","Movie","sound"]:
                if stimType in componentClassString:
                    supportedStimType = True
                    thisComponent.elOnsetDetected = False
                    thisComponent.elOffsetDetected = False
                    if thisComponent in componentsForEyeLinkInterestAreaMessages:
                        thisComponent.iaInstanceStartTime = -1
                        thisComponent.iaIndex = componentsForEyeLinkInterestAreaMessages.index(thisComponent) + 1
                    if stimType != "sound":
                        thisComponent.elPos = eyelink_pos(thisComponent.pos,[scn_width,scn_height])
                        thisComponent.elSize = eyelink_size(thisComponent.size,[scn_width,scn_height])
                        thisComponent.lastelPos = thisComponent.elPos
                        thisComponent.lastelSize = thisComponent.elSize
                    if stimType == "MovieStim3":
                        thisComponent.componentType = "MovieStim3"
                        thisComponent.elMarkingFrameIndex = -1
                        thisComponent.previousFrameTime = 0
                        thisComponent.firstFramePresented = False
                        componentsForEyeLinkMovieFrameMarking.append(thisComponent)   
                    elif stimType == "Movie":
                        thisComponent.componentType = "MovieStimWithFrameNum"
                        thisComponent.elMarkingFrameIndex = -1
                        thisComponent.firstFramePresented = False
                        componentsForEyeLinkMovieFrameMarking.append(thisComponent)
                    else:
                        thisComponent.componentType = stimType
                    break   
            if not supportedStimType:
                print("WARNING:  Stimulus component type " + str(thisComponent.__class__) + " not supported for EyeLink event marking")
                print("          Event timing messages and/or Data Viewer drawing messages")
                print("          will not be marked for this component")
                print("          Consider marking the component via code component")
                # remove unsupported types from our monitoring lists
                allStimComponentsForEyeLinkMonitoring.remove(thisComponent)
                componentsForEyeLinkStimEventMessages.remove(thisComponent)
                componentsForEyeLinkStimDVDrawingMessages.remove(thisComponent)
                componentsForEyeLinkInterestAreaMessages.remove(thisComponent)
        
        # Set Interest Area Margin -- this value will be added to all four edges of the components
        # for which interest areas will be created
        interestAreaMargins = 0
        
        # Initialize response components whose occurence needs to be marked with 
        # a message to the EDF (provided they are supported stimulus types)
        # Supported types include mouse, keyboard, and any response component with an RT or time property
        for thisComponent in componentsForEyeLinkRespEventMessages:
            componentClassString = str(thisComponent.__class__)
            componentClassDir = dir(thisComponent)
            supportedRespType = False
            for respType in ["Mouse","Keyboard"]:
                if respType in componentClassString:
                    thisComponent.componentType = respType
                    supportedRespType = True
                    break
            if not supportedRespType:
                if "rt" in componentClassDir:
                    thisComponent.componentType = "OtherRespWithRT"
                    supportedRespType = True
                elif "time" in componentClassDir:
                    thisComponent.componentType = "OtherRespWithTime"
                    supportedRespType = True
            if not supportedRespType:    
                    print("WARNING:  Response component type " + str(thisComponent.__class__) + " not supported for EyeLink event marking")
                    print("          Event timing will not be marked for this component")
                    print("          Please consider marking the component via code component")
                    # remove unsupported response types
                    componentsForEyeLinkRespEventMessages.remove(thisComponent)
        
        # Open a draw list file (DLF) to which Data Viewer drawing information will be logged
        # The commands that will be written to this DLF file will enable
        # Data Viewer to reproduce the stimuli in its Trial View window
        sentDrawListMessage = False
        # create a folder for the current testing session in the "results" folder
        drawList_folder = os.path.join(results_folder, session_identifier,"graphics")
        if not os.path.exists(drawList_folder):
            os.makedirs(drawList_folder)
        # open a DRAW LIST file to save the frame timing info for the video, which will
        # help us to be able to see the video in Data Viewer's Trial View window
        # See the Data Viewer User Manual section:
        # "Procotol for EyeLink Data to Viewer Integration -> Simple Drawing Commands"
        dlf = 'TRIAL_%04d_ROUTINE_%02d.dlf' % (trial_index,routine_index)
        dlf_file = open(os.path.join(drawList_folder, dlf), 'w')
        
        # Open an Interest Area Set (IAS) file to which interest area information will be logged
        # Interest Areas will appear in Data Viewer and assist with analysis
        # See the Data Viewer User Manual section: 
        # "Procotol for EyeLink Data to Viewer Integration -> Interest Area Commands"
        sentIASFileMessage = False
        interestAreaSet_folder = os.path.join(results_folder, session_identifier,"aoi")
        if not os.path.exists(interestAreaSet_folder):
            os.makedirs(interestAreaSet_folder)
        # open the IAS file to save the interest area info for the stimuli
        ias = 'TRIAL_%04d_ROUTINE_%02d.ias' % (trial_index,routine_index)
        ias_file = open(os.path.join(interestAreaSet_folder, ias), 'w')
        # Update a routine index for EyeLink IAS/DLF file logging -- 
        # Each routine will have its own set of IAS/DLF files, as each will have its own  Mark Events component
        routine_index = routine_index + 1
        # Send a Data Viewer clear screen command to clear its Trial View window
        # to the window color
        el_tracker.sendMessage('!V CLEAR %d %d %d' % eyelink_color(win.color))
        # create a keyboard instance and reinitialize a kePressNameList, which
        # will store list of key names currently being pressed (to allow Ctrl-C abort)
        kb = keyboard.Keyboard()
        keyPressNameList = []
        eyelinkThisFrameCallOnFlipScheduled = False
        eyelinkLastFlipTime = 0.0
        routineTimer.reset()
        # store start times for S1_image_display
        S1_image_display.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        S1_image_display.tStart = globalClock.getTime(format='float')
        S1_image_display.status = STARTED
        thisExp.addData('S1_image_display.started', S1_image_display.tStart)
        S1_image_display.maxDuration = None
        # keep track of which components have finished
        S1_image_displayComponents = S1_image_display.components
        for thisComponent in S1_image_display.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "S1_image_display" ---
        # if trial has changed, end Routine now
        if isinstance(experiment_loop, data.TrialHandler2) and thisExperiment_loop.thisN != experiment_loop.thisTrial.thisN:
            continueRoutine = False
        S1_image_display.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *s1_crosshair* updates
            
            # if s1_crosshair is starting this frame...
            if s1_crosshair.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                s1_crosshair.frameNStart = frameN  # exact frame index
                s1_crosshair.tStart = t  # local t and not account for scr refresh
                s1_crosshair.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(s1_crosshair, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 's1_crosshair.started')
                # update status
                s1_crosshair.status = STARTED
                s1_crosshair.setAutoDraw(True)
            
            # if s1_crosshair is active this frame...
            if s1_crosshair.status == STARTED:
                # update params
                pass
            
            # if s1_crosshair is stopping this frame...
            if s1_crosshair.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > s1_crosshair.tStartRefresh + fixDur-frameTolerance:
                    # keep track of stop time/frame for later
                    s1_crosshair.tStop = t  # not accounting for scr refresh
                    s1_crosshair.tStopRefresh = tThisFlipGlobal  # on global time
                    s1_crosshair.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 's1_crosshair.stopped')
                    # update status
                    s1_crosshair.status = FINISHED
                    s1_crosshair.setAutoDraw(False)
            
            # *s1_image* updates
            
            # if s1_image is starting this frame...
            if s1_image.status == NOT_STARTED and tThisFlip >= fixDur+4-frameTolerance:
                # keep track of start time/frame for later
                s1_image.frameNStart = frameN  # exact frame index
                s1_image.tStart = t  # local t and not account for scr refresh
                s1_image.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(s1_image, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 's1_image.started')
                # update status
                s1_image.status = STARTED
                s1_image.setAutoDraw(True)
            
            # if s1_image is active this frame...
            if s1_image.status == STARTED:
                # update params
                pass
            
            # *movie* updates
            
            # if movie is starting this frame...
            if movie.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                movie.frameNStart = frameN  # exact frame index
                movie.tStart = t  # local t and not account for scr refresh
                movie.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(movie, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'movie.started')
                # update status
                movie.status = STARTED
                movie.setAutoDraw(True)
                movie.play()
            
            # if movie is stopping this frame...
            if movie.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > movie.tStartRefresh + 4-frameTolerance or movie.isFinished:
                    # keep track of stop time/frame for later
                    movie.tStop = t  # not accounting for scr refresh
                    movie.tStopRefresh = tThisFlipGlobal  # on global time
                    movie.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'movie.stopped')
                    # update status
                    movie.status = FINISHED
                    movie.setAutoDraw(False)
                    movie.stop()
            # This section of EyeLink MarkEvents_2 component code checks whether to send (and sends/logs when appropriate)
            # event marking messages, log Data Viewer (DV) stimulus drawing info, log DV interest area info,
            # send DV Target Position Messages, and/or log DV video frame marking info
            if not eyelinkThisFrameCallOnFlipScheduled:
                # This method, created by the EyeLink MarkEvents_2 component code will get called to handle
                # sending event marking messages, logging Data Viewer (DV) stimulus drawing info, logging DV interest area info,
                # sending DV Target Position Messages, and/or logging DV video frame marking info=information
                win.callOnFlip(eyelink_onFlip_MarkEvents_2,globalClock,win,scn_width,scn_height,allStimComponentsForEyeLinkMonitoring,\
                    componentsForEyeLinkStimEventMessages,\
                    componentsForEyeLinkStimDVDrawingMessages,dlf,dlf_file,\
                    componentsForEyeLinkInterestAreaMessages,ias,ias_file,interestAreaMargins,\
                componentsForEyeLinkMovieFrameMarking)
                eyelinkThisFrameCallOnFlipScheduled = True
            
            # abort the current trial if the tracker is no longer recording
            error = el_tracker.isRecording()
            if error is not pylink.TRIAL_OK:
                el_tracker.sendMessage('tracker_disconnected')
                abort_trial(win,genv)
            
            # check keyboard events for experiment abort key combination
            keyPressList = kb.getKeys(keyList = ['lctrl','rctrl','c'], waitRelease = False, clear = False)
            for keyPress in keyPressList:
                keyPressName = keyPress.name
                if keyPressName not in keyPressNameList:
                    keyPressNameList.append(keyPress.name)
            if ('lctrl' in keyPressNameList or 'rctrl' in keyPressNameList) and 'c' in keyPressNameList:
                el_tracker.sendMessage('terminated_by_user')
                terminate_task(win,genv,edf_file,session_folder,session_identifier)
            #check for key releases
            keyReleaseList = kb.getKeys(keyList = ['lctrl','rctrl','c'], waitRelease = True, clear = False)
            for keyRelease in keyReleaseList:
                keyReleaseName = keyRelease.name
                if keyReleaseName in keyPressNameList:
                    keyPressNameList.remove(keyReleaseName)
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[movie]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                S1_image_display.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in S1_image_display.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "S1_image_display" ---
        for thisComponent in S1_image_display.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for S1_image_display
        S1_image_display.tStop = globalClock.getTime(format='float')
        S1_image_display.tStopRefresh = tThisFlipGlobal
        thisExp.addData('S1_image_display.stopped', S1_image_display.tStop)
        movie.stop()  # ensure movie has stopped at end of Routine
        
        # This section of EyeLink MarkEvents_2 component code does some event cleanup at the end of the routine
        # Go through all stimulus components that need to be checked for event marking,
        #  to see if the trial ended before PsychoPy reported OFFSET detection to mark their offset from trial end
        for thisComponent in componentsForEyeLinkStimEventMessages:
            if thisComponent.elOnsetDetected and not thisComponent.elOffsetDetected:
                # Check if the component had onset but the trial ended before offset
                el_tracker.sendMessage('%s_OFFSET' % (thisComponent.name))
        # Go through all response components whose occurence/data
        # need to be logged to the EDF and marks their occurence with a message (using an offset calculation that backstam
        for thisComponent in componentsForEyeLinkRespEventMessages:
            if thisComponent.componentType == "Keyboard" or thisComponent.componentType == "OtherRespWithRT":
                if not isinstance(thisComponent.rt,list):
                    offsetValue = int(round((globalClock.getTime() - \
                        (thisComponent.tStartRefresh + thisComponent.rt))*1000))
                    el_tracker.sendMessage('%i %s_EVENT' % (offsetValue,thisComponent.componentType,))
                    # if sending many messages in a row, add a 1 msec pause between after
                    # every 5 messages or so
                if isinstance(thisComponent.rt,list) and len(thisComponent.rt) > 0:
                    for i in range(len(thisComponent.rt)):
                        offsetValue = int(round((globalClock.getTime() - \
                            (thisComponent.tStartRefresh + thisComponent.rt[i]))*1000))
                        el_tracker.sendMessage('%i %s_EVENT_%i' % (offsetValue,thisComponent.componentType,i+1))
                        if i % 4 == 0:
                            # if sending many messages in a row, add a 1 msec pause between after 
                            # every 5 messages or so
                            time.sleep(0.001)
                el_tracker.sendMessage('!V TRIAL_VAR %s.rt(s) %s' % (thisComponent.componentType,thisComponent.rt))
                if "corr" in dir(thisComponent):
                    el_tracker.sendMessage('!V TRIAL_VAR %s.corr %s' % (thisComponent.componentType,thisComponent.corr))
                if "keys" in dir(thisComponent):
                    el_tracker.sendMessage('!V TRIAL_VAR %s.keys %s' % (thisComponent.componentType,thisComponent.keys))
            elif thisComponent.componentType == "Mouse" or thisComponent.componentType == "OtherRespWithTime":
                if not isinstance(thisComponent.time,list):
                    offsetValue = int(round((globalClock.getTime() - \
                        (thisComponent.tStartRefresh + thisComponent.time))*1000))
                    el_tracker.sendMessage('%i %s_EVENT' % (thisComponent.componentType,offsetValue))
                    # if sending many messages in a row, add a 1 msec pause between after 
                    # every 5 messages or so
                    time.sleep(0.0005)
                if isinstance(thisComponent.time,list) and len(thisComponent.time) > 0:
                    for i in range(len(thisComponent.time)):
                        offsetValue = int(round((globalClock.getTime() - \
                            (thisComponent.tStartRefresh + thisComponent.time[i]))*1000))
                        el_tracker.sendMessage('%i %s_EVENT_%i' % (offsetValue,thisComponent.componentType,i+1))
                        if i % 4 == 0:
                            # if sending many messages in a row, add a 1 msec pause between after 
                            # every 5 messages or so
                            time.sleep(0.001)
                el_tracker.sendMessage('!V TRIAL_VAR %s.time(s) %s' % (thisComponent.componentType,thisComponent.time))
            time.sleep(0.001)
        
        # log any remaining interest area commands to the IAS file for stimuli that 
        # were still being presented when the routine ended
        for thisComponent in componentsForEyeLinkInterestAreaMessages:
            if not thisComponent.elOffsetDetected and thisComponent.tStartRefresh is not None:
                ias_file.write('%i %i IAREA %s %i %i %i %i %i %s\n' % \
                    (int(round((zeroTimeIAS - thisComponent.iaInstanceStartTime)*1000)),
                    int(round((zeroTimeIAS - globalClock.getTime())*1000 - 1)),"RECTANGLE",thisComponent.iaIndex,
                    thisComponent.elPos[0]-(thisComponent.elSize[0]/2+interestAreaMargins),
                    thisComponent.elPos[1]-(thisComponent.elSize[1]/2+interestAreaMargins),
                    thisComponent.elPos[0]+(thisComponent.elSize[0]/2+interestAreaMargins),
                    thisComponent.elPos[1]+(thisComponent.elSize[1]/2+interestAreaMargins),thisComponent.name))
        # Close the interest area set file and draw list file for the trial
        ias_file.close()
        # close the drawlist file (which is used in Data Viewer stimulus presntation re-creation)
        dlf_file.close()
        
        # the Routine "S1_image_display" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        
        # --- Prepare to start Routine "S1_eye_link_stop" ---
        # create an object to store info about Routine S1_eye_link_stop
        S1_eye_link_stop = data.Routine(
            name='S1_eye_link_stop',
            components=[StopRecord_2],
        )
        S1_eye_link_stop.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for S1_eye_link_stop
        S1_eye_link_stop.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        S1_eye_link_stop.tStart = globalClock.getTime(format='float')
        S1_eye_link_stop.status = STARTED
        thisExp.addData('S1_eye_link_stop.started', S1_eye_link_stop.tStart)
        S1_eye_link_stop.maxDuration = None
        # keep track of which components have finished
        S1_eye_link_stopComponents = S1_eye_link_stop.components
        for thisComponent in S1_eye_link_stop.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "S1_eye_link_stop" ---
        # if trial has changed, end Routine now
        if isinstance(experiment_loop, data.TrialHandler2) and thisExperiment_loop.thisN != experiment_loop.thisTrial.thisN:
            continueRoutine = False
        S1_eye_link_stop.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 0.001:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                S1_eye_link_stop.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in S1_eye_link_stop.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "S1_eye_link_stop" ---
        for thisComponent in S1_eye_link_stop.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for S1_eye_link_stop
        S1_eye_link_stop.tStop = globalClock.getTime(format='float')
        S1_eye_link_stop.tStopRefresh = tThisFlipGlobal
        thisExp.addData('S1_eye_link_stop.stopped', S1_eye_link_stop.tStop)
        # This section of EyeLink StopRecord_2 component code stops recording, sends a trial end (TRIAL_RESULT)
        # message to the EDF, and updates the trial_index variable 
        el_tracker.stopRecording()
        
        # send a 'TRIAL_RESULT' message to mark the end of trial, see Data
        # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
        el_tracker.sendMessage('TRIAL_RESULT %d' % 0)
        
        # update the trial counter for the next trial
        trial_index = trial_index + 1
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if S1_eye_link_stop.maxDurationReached:
            routineTimer.addTime(-S1_eye_link_stop.maxDuration)
        elif S1_eye_link_stop.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-0.001000)
        
        # --- Prepare to start Routine "inter_trial_interval" ---
        # create an object to store info about Routine inter_trial_interval
        inter_trial_interval = data.Routine(
            name='inter_trial_interval',
            components=[blank_iti],
        )
        inter_trial_interval.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # store start times for inter_trial_interval
        inter_trial_interval.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        inter_trial_interval.tStart = globalClock.getTime(format='float')
        inter_trial_interval.status = STARTED
        thisExp.addData('inter_trial_interval.started', inter_trial_interval.tStart)
        inter_trial_interval.maxDuration = None
        # keep track of which components have finished
        inter_trial_intervalComponents = inter_trial_interval.components
        for thisComponent in inter_trial_interval.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "inter_trial_interval" ---
        # if trial has changed, end Routine now
        if isinstance(experiment_loop, data.TrialHandler2) and thisExperiment_loop.thisN != experiment_loop.thisTrial.thisN:
            continueRoutine = False
        inter_trial_interval.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *blank_iti* updates
            
            # if blank_iti is starting this frame...
            if blank_iti.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                blank_iti.frameNStart = frameN  # exact frame index
                blank_iti.tStart = t  # local t and not account for scr refresh
                blank_iti.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(blank_iti, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'blank_iti.started')
                # update status
                blank_iti.status = STARTED
                blank_iti.setAutoDraw(True)
            
            # if blank_iti is active this frame...
            if blank_iti.status == STARTED:
                # update params
                pass
            
            # if blank_iti is stopping this frame...
            if blank_iti.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > blank_iti.tStartRefresh + iti-frameTolerance:
                    # keep track of stop time/frame for later
                    blank_iti.tStop = t  # not accounting for scr refresh
                    blank_iti.tStopRefresh = tThisFlipGlobal  # on global time
                    blank_iti.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'blank_iti.stopped')
                    # update status
                    blank_iti.status = FINISHED
                    blank_iti.setAutoDraw(False)
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                inter_trial_interval.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in inter_trial_interval.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "inter_trial_interval" ---
        for thisComponent in inter_trial_interval.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for inter_trial_interval
        inter_trial_interval.tStop = globalClock.getTime(format='float')
        inter_trial_interval.tStopRefresh = tThisFlipGlobal
        thisExp.addData('inter_trial_interval.stopped', inter_trial_interval.tStop)
        # the Routine "inter_trial_interval" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        thisExp.nextEntry()
        
    # completed 1.0 repeats of 'experiment_loop'
    
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    # get names of stimulus parameters
    if experiment_loop.trialList in ([], [None], None):
        params = []
    else:
        params = experiment_loop.trialList[0].keys()
    # save data for this loop
    experiment_loop.saveAsExcel(filename + '.xlsx', sheetName='experiment_loop',
        stimOut=params,
        dataOut=['n','all_mean','all_std', 'all_raw'])
    experiment_loop.saveAsText(filename + 'experiment_loop.csv', delim=',',
        stimOut=params,
        dataOut=['n','all_mean','all_std', 'all_raw'])
    
    # --- Prepare to start Routine "thanks" ---
    # create an object to store info about Routine thanks
    thanks = data.Routine(
        name='thanks',
        components=[textbox],
    )
    thanks.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    textbox.reset()
    # store start times for thanks
    thanks.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    thanks.tStart = globalClock.getTime(format='float')
    thanks.status = STARTED
    thisExp.addData('thanks.started', thanks.tStart)
    thanks.maxDuration = None
    # keep track of which components have finished
    thanksComponents = thanks.components
    for thisComponent in thanks.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "thanks" ---
    thanks.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 5.0:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *textbox* updates
        
        # if textbox is starting this frame...
        if textbox.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            textbox.frameNStart = frameN  # exact frame index
            textbox.tStart = t  # local t and not account for scr refresh
            textbox.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(textbox, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'textbox.started')
            # update status
            textbox.status = STARTED
            textbox.setAutoDraw(True)
        
        # if textbox is active this frame...
        if textbox.status == STARTED:
            # update params
            pass
        
        # if textbox is stopping this frame...
        if textbox.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > textbox.tStartRefresh + 5.0-frameTolerance:
                # keep track of stop time/frame for later
                textbox.tStop = t  # not accounting for scr refresh
                textbox.tStopRefresh = tThisFlipGlobal  # on global time
                textbox.frameNStop = frameN  # exact frame index
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'textbox.stopped')
                # update status
                textbox.status = FINISHED
                textbox.setAutoDraw(False)
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            thanks.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in thanks.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "thanks" ---
    for thisComponent in thanks.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for thanks
    thanks.tStop = globalClock.getTime(format='float')
    thanks.tStopRefresh = tThisFlipGlobal
    thisExp.addData('thanks.stopped', thanks.tStop)
    # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
    if thanks.maxDurationReached:
        routineTimer.addTime(-thanks.maxDuration)
    elif thanks.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-5.000000)
    thisExp.nextEntry()
    # This section of the Initialize component calls the 
    # terminate_task helper function to get the EDF file and close the connection
    # to the Host PC
    
    # Disconnect, download the EDF file, then terminate the task
    terminate_task(win,genv,edf_file,session_folder,session_identifier)
    
    # mark experiment as finished
    endExperiment(thisExp, win=win)


def saveData(thisExp):
    """
    Save data from this experiment
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    filename = thisExp.dataFileName
    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.
    
    This function does NOT close the window or end the Python process - use `quit` for this.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    """
    if win is not None:
        # remove autodraw from all current components
        win.clearAutoDraw()
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed
        win.flip()
    # return console logger level to WARNING
    logging.console.setLevel(logging.WARNING)
    # mark experiment handler as finished
    thisExp.status = FINISHED
    logging.flush()


def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.
    
    Parameters
    ==========
    win : psychopy.visual.Window
        Window to close.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    thisExp.abort()  # or data files will save again on exit
    # make sure everything is closed down
    if win is not None:
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed before quitting
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    # terminate Python process
    core.quit()


# if running this experiment as a script...
if __name__ == '__main__':
    # call all functions in order
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo, 
        thisExp=thisExp, 
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)
