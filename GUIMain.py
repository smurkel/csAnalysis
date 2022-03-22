import tkinter as tk
from tkinter import filedialog

import glfw
import OpenGL.GL as gl
import imgui
import config as cfg
from imgui.integrations.glfw import GlfwRenderer
import pickle
from Core import *
import params as prm
import Reconstruction
import Renderer
import Input
import AnalysisMethods

tkroot = tk.Tk()
tkroot.withdraw()

def Start():
    window_name = "csAnalysis"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    if cfg.fullscreen:
        window = glfw.create_window(int(cfg.window_width), int(cfg.window_height), cfg.window_name, glfw.get_primary_monitor(), None)
    else:
        window = glfw.create_window(int(cfg.window_width), int(cfg.window_height), cfg.window_name, None, None);
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    imgui.create_context()
    prm.m_window = window
    prm.m_impl = GlfwRenderer(window)
    Renderer.Init()

def OnUpdate():
    if glfw.window_should_close(prm.m_window):
        return False

    prm.m_impl.process_inputs()
    imgui.new_frame()
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File", True):
            newProject, _ = imgui.menu_item("New project")
            if newProject:
                clb_newProject()
            loadProject, _ = imgui.menu_item("Load project")
            if loadProject:
                clb_loadProject()
            saveProject, _ = imgui.menu_item("Save project")
            if saveProject:
                clb_saveProject()
            imgui.end_menu()
        imgui.end_main_menu_bar()
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    # Custom implementation here
    if prm.current_project:
        AnalysisMain()
        ImageViewer()
        TimelineControls()
        ImageRenderControls()
    # End custom implementation section
    imgui.render()
    prm.m_impl.render(imgui.get_draw_data())
    glfw.swap_buffers(prm.m_window)
    return True

def End():
    prm.m_impl.shutdown()
    glfw.terminate()

def clb_newProject():
    filename = filedialog.askopenfilename()
    if filename:
        prm.current_project = Reconstruction.Project(filename)
        Renderer.BindImage(prm.current_project.current_img_data)
        cfg.current_frame = 1
        prm.framesselected = prm.current_project.framesselected
        prm.registered = prm.current_project.registered
    glfw.focus_window(prm.m_window)

def clb_loadProject():
    filename = filedialog.askopenfilename()
    if filename:
        with open(filename, 'rb') as proj:
            prm.current_project = pickle.load(proj)
            Renderer.BindImage(prm.current_project.current_img_data)
            cfg.current_frame = prm.current_project.current_img_id
            prm.framesselected = prm.current_project.framesselected
            prm.registered = prm.current_project.registered
            prm.current_project.genTimelineTexture()
    glfw.focus_window(prm.m_window)

def clb_saveProject():
    filename = filedialog.asksaveasfilename()
    if filename:
        with open(filename, 'wb') as proj:
            pickle.dump(prm.current_project, proj)
    glfw.focus_window(prm.m_window)

############################################################################################################################################
############################################################################################################################################
############################################################# Analysis modules #############################################################
############################################################################################################################################
############################################################################################################################################

def AnalysisMain():
    def _pushHeaderColor(colourtuple):
        imgui.push_style_color(imgui.COLOR_HEADER, *colourtuple)
        imgui.push_style_color(imgui.COLOR_HEADER_ACTIVE, *colourtuple)
        imgui.push_style_color(imgui.COLOR_HEADER_HOVERED, *colourtuple)
    def _popHeaderColor():
        imgui.pop_style_color(3)

    imgui.begin("Analysis", flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
    ### STAGE 0 - PREPARATION
    # Project settings
    _pushHeaderColor(cfg.clr_stage_stackpreparation)
    expanded, _ = imgui.collapsing_header("Project settings")
    if expanded:
        Analysis_ProjectSettings()

    # Frame selection
    expanded, _ = imgui.collapsing_header("Frame selection")
    if expanded:
        Analysis_FrameSelection()

    # Registration
    expanded, _ = imgui.collapsing_header("Registration")
    if expanded:
        Analysis_Registration()


    # Filters
    expanded, _ = imgui.collapsing_header("Filtering")
    if expanded:
        Analysis_Filtering()
    _popHeaderColor()

    ### MISC STAGES
    _pushHeaderColor(cfg.clr_stage_misc)
    # Plots
    expanded, _ = imgui.collapsing_header("Plots")
    if expanded:
        Analysis_Plots()


    # Debug
    expanded, _ = imgui.collapsing_header("Debug")
    if expanded:
        DebugGUI()
    _popHeaderColor()
    imgui.end()


def Analysis_ProjectSettings():
    imgui.text("ROI selection")
    roi = [*prm.current_project.roi]
    _a, roi[0] = imgui.slider_int("x min", roi[0], 0, prm.current_project.width)
    _b, roi[2] = imgui.slider_int("x max", roi[2], 0, prm.current_project.width)
    _c, roi[1] = imgui.slider_int("y min", roi[1], 0, prm.current_project.height)
    _d, roi[3] = imgui.slider_int("y max", roi[3], 0, prm.current_project.height)
    if _a or _b or _c or _d:
        xmin = max([roi[0], 0])
        xmax = min([roi[2], prm.current_project.width])
        ymin = max([roi[1], 0])
        ymax = min([roi[3], prm.current_project.height])
        prm.current_project.roi = (xmin, ymin, xmax, ymax)
    if imgui.button("Maximize ROI", 250, 20):
        prm.current_project.roi = (0, 0, prm.current_project.width, prm.current_project.height)
    imgui.spacing()
    imgui.text("Acquisition parameters")

    imgui.push_item_width(100)
    _, prm.current_project.pixelsize = imgui.input_float("pixel size (nm)", prm.current_project.pixelsize, format = "%.0f")
    _, prm.current_project.framespercycle = imgui.input_int("frames per cycle", prm.current_project.framespercycle)
    imgui.spacing()
    imgui.pop_item_width()

def Analysis_FrameSelection():
    windowWidth = imgui.get_window_content_region_width()
    imgui.text("Settings")
    imgui.text("Filter by name")
    imgui.push_id("filter selection")
    # Filter
    _, cfg.selection_filter = imgui.input_text("filter", cfg.selection_filter, 256)

    imgui.push_item_width(cfg.selection_combo_width)
    _, cfg.selection_selected_option = imgui.combo("##filteroption", cfg.selection_selected_option, cfg.selection_filter_options)
    imgui.same_line()
    applyFilter = imgui.button("apply", cfg.selection_apply_button_width,cfg.selection_apply_button_height)
    if applyFilter:
        AnalysisMethods.ApplyFilter()

    imgui.pop_id()
    imgui.spacing()
    imgui.push_id("range selection")
    imgui.text("Filter by range")
    _, cfg.selection_range = imgui.input_int2("Range [_,_)", *cfg.selection_range)
    imgui.push_item_width(cfg.selection_combo_width)
    _, cfg.selection_selected_option_range = imgui.combo("##rangeoption", cfg.selection_selected_option_range,cfg.selection_filter_options)
    imgui.same_line()
    applyRange = imgui.button("apply", cfg.selection_apply_button_width, cfg.selection_apply_button_height)
    imgui.pop_id()
    imgui.spacing()
    if applyRange:
        AnalysisMethods.ApplyRange()

    imgui.spacing()
    imgui.spacing()

    imgui.separator()
    imgui.text("Actions")
    imgui.new_line()
    imgui.same_line(position = int((windowWidth - cfg.selection_bake_button_width) / 2))
    bakeSelection = imgui.button("Bake applied filters", cfg.selection_bake_button_width, cfg.selection_bake_button_height)
    imgui.new_line()
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    clearFilters = imgui.button("Clear applied filters", cfg.selection_bake_button_width,cfg.selection_bake_button_height)
    imgui.new_line()
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    undoBake = imgui.button("Recover all frames", cfg.selection_bake_button_width,
                                cfg.selection_bake_button_height)
    if bakeSelection:
        AnalysisMethods.BakeSelection()
        prm.current_project.framesselected = True
        prm.framesselected = True
    if clearFilters:
        AnalysisMethods.ClearFilters()
    if undoBake:
        AnalysisMethods.UndoBake()
    imgui.spacing()
    imgui.spacing()

def Analysis_Registration():
    windowWidth = imgui.get_window_content_region_width()
    if cfg.registration_running:
        imgui.push_style_color(imgui.COLOR_TEXT, *cfg.clr_disabled_text)
        imgui.push_style_color(imgui.COLOR_BUTTON, *cfg.clr_disabled)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, *cfg.clr_disabled)
        imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, *cfg.clr_disabled)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND, *cfg.clr_disabled)
        imgui.push_style_color(imgui.COLOR_FRAME_BACKGROUND_HOVERED, *cfg.clr_disabled)
    imgui.text("Settings")
    imgui.text("Select frame pairing method")
    _, cfg.registration_matching_selected_option = imgui.combo("frame matching", cfg.registration_matching_selected_option, cfg.registration_matching_options)
    if cfg.registration_matching_selected_option == 2:
        _, cfg.registration_matching_selected_frame = imgui.input_int("reference ID", cfg.registration_matching_selected_frame, step = 0)
    imgui.push_item_width(140)
    _, cfg.registration_parallel_processes = imgui.input_int("Parallel processes", cfg.registration_parallel_processes)
    imgui.pop_item_width()
    if imgui.is_item_hovered() and not imgui.is_item_active():
        imgui.set_tooltip("Images are processed in batches of this size. Increasing the value reduces\nduration of the registration, but also increases the degree of blocking of\nthe program during the computation. A batch size larger than the amount of\nCPU cores and not an integer multiple of the amount of cores leads to\ninefficient batch processing.")
    cfg.registration_parallel_processes = max([1, cfg.registration_parallel_processes])

    imgui.spacing()

    imgui.separator()
    imgui.text("Actions")
    imgui.new_line()
    # Register button
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    startRegistration = imgui.button("Register stack", cfg.registration_start_button_width, cfg.registration_start_button_height)
    imgui.spacing()

    # Export stack registered
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    saveRegisteredStack = imgui.button("Export registered stack", cfg.registration_start_button_width, cfg.registration_start_button_height)
    imgui.spacing()

    # Export sample movement
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    exportMovement = imgui.button("Export sample movement", cfg.registration_start_button_width, cfg.registration_start_button_height)
    imgui.spacing()

    if cfg.registration_running:
        imgui.pop_style_color(6)
        imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
        cancelRegistration = imgui.button("Stop registration", cfg.registration_start_button_width,
                                          cfg.registration_start_button_height)
        imgui.text("Progress: {} / {} images registered".format(cfg.registration_imgs_registered, cfg.registration_imgs_to_reg_total))
        imgui.spacing()
        if cancelRegistration:
            cfg.registration_running = False
    if not cfg.registration_running:
        if saveRegisteredStack:
            filepath = filedialog.asksaveasfilename()
            glfw.focus_window(prm.m_window)
            if filepath:
                AnalysisMethods.SaveRegistration(filepath)
        if exportMovement:
            filepath = filedialog.asksaveasfilename()
            glfw.focus_window(prm.m_window)
            if filepath:
                AnalysisMethods.SaveMovement(filepath)
        if startRegistration:
            AnalysisMethods.StartRegistration()

def Analysis_Filtering():
    windowWidth = imgui.get_window_content_region_width()
    imgui.text("Settings")
    imgui.separator()
    imgui.push_item_width(cfg.fltr_combo_width)
    _, cfg.fltr_selected = imgui.combo("Filter", cfg.fltr_selected, cfg.fltr_options)
    if cfg.fltr_selected == 1 or cfg.fltr_selected == 2:
        _, cfg.fltr_neg_offset = imgui.input_int("Offset", cfg.fltr_neg_offset)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Before filtering the image, an offset value can be added to the every pixel\nin order to avoid negative values in the result.")
        _, cfg.fltr_neg_selected = imgui.combo("Negative value mask", cfg.fltr_neg_selected, cfg.fltr_negative_options)

    imgui.pop_item_width()
    imgui.spacing()
    imgui.spacing()
    imgui.separator()
    imgui.text("Actions")
    imgui.new_line()
    imgui.same_line(position=int((windowWidth - cfg.selection_bake_button_width) / 2))
    applyImgFilter = imgui.button("Apply filter", width = cfg.selection_bake_button_width, height = cfg.selection_bake_button_height)

    cfg.fltr_applied = cfg.fltr_selected
    prm.current_project.update()

def Analysis_Plots():
    windowWidth = imgui.get_window_content_region_width()
    imgui.spacing()
    imgui.text("General")
    plotMovement = imgui.button("Plot sample movement", cfg.registration_start_button_width, cfg.registration_start_button_height)
    if plotMovement:
        if prm.current_project.registered:
            AnalysisMethods.PlotMovement()

    # Plot intensity over time
    plotIntensity = imgui.button("Plot bulk intensity", cfg.registration_start_button_width,cfg.registration_start_button_height)
    if plotIntensity:
        AnalysisMethods.PlotIntensity()
    imgui.spacing()
    imgui.separator()
    imgui.text("Misc. plots")

    plotMovementSpectrum = imgui.button("Plot vibrations", cfg.registration_start_button_width, cfg.registration_start_button_height)
    imgui.same_line()
    imgui.push_item_width(30)
    _, cfg.frametime = imgui.input_int("frametime (ms)", cfg.frametime, 0, 0)
    imgui.pop_item_width()
    if plotMovementSpectrum:
        if prm.current_project.registered:
            AnalysisMethods.PlotMovementSpectrum()
    imgui.spacing()
def DebugGUI():
    if (imgui.button("recompile shader", 50, 50)):
        Renderer.RecompileShader()
    _, cfg.debu1 = imgui.slider_float("sdav", cfg.debu1, 0.0, 65535.0)
############################################################################################################################################
############################################################################################################################################
############################################################### Image viewer ###############################################################
############################################################### and timeline ###############################################################
############################################################################################################################################
############################################################################################################################################

def ImageViewer():
    Renderer.Render()
    # Input
    if not imgui.get_io().want_capture_mouse:
        # Pan controls:
        if Input.getMousePressed(0):
            cfg.screenView_xCenter -= cfg.screenView_translate_speed * Input.cursorOffset[0]
            cfg.screenView_yCenter += cfg.screenView_translate_speed * Input.cursorOffset[1]
            Input.scrollOffset = [0.0, 0.0]
        # Zoom controls. Default is smooth zoom, pressing left_shift removes the smooth.
        if Input.getKeyPressed(Input.KEY_LEFT_SHIFT):
            cfg.screenView_zoom *= (1.0 + Input.scrollOffset[1] * cfg.screenView_zoom_speed_discrete)
            Input.scrollOffset = [0.0, 0.0]
        elif Input.getKeyPressed(Input.KEY_LEFT_CTRL):
            if Input.scrollOffset[1] > 0:
                Timeline_setFrame(cfg.current_frame - 10)
            elif Input.scrollOffset[1] < 0:
                Timeline_setFrame(cfg.current_frame + 10)
        else:
            if Input.scrollOffset[1] > 0:
                Timeline_setFrame(cfg.current_frame - 1)
            elif Input.scrollOffset[1] < 0:
                Timeline_setFrame(cfg.current_frame + 1)


def TimelineControls():
    imgui.begin("Timeline controls", flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
    windowWidth = imgui.get_content_region_available_width()
    imgui.image(prm.timelineTex.renderer_id, windowWidth, 20)
    timeline_zoom_uv_center = cfg.current_frame / prm.current_project.n_images
    timeline_zoom_uv_window = 1.0 / (2 * cfg.timeline_focus_magnification)
    timeline_zoom_uv_tl = (timeline_zoom_uv_center - timeline_zoom_uv_window, 0.0)
    timeline_zoom_uv_br = (timeline_zoom_uv_center + timeline_zoom_uv_window, 1.0)
    imgui.image(prm.timelineTex.renderer_id, windowWidth, 20, timeline_zoom_uv_tl, timeline_zoom_uv_br)
    currentImage = prm.current_project.active_images[cfg.current_frame]
    # Frame selection
    imgui.push_item_width(windowWidth)
    _showNewFrame, cfg.current_frame = imgui.slider_int("##frameSelector", cfg.current_frame, 0, prm.current_project.n_images-1, format = "frame {}/{}".format(cfg.current_frame + 1, prm.current_project.n_images))
    imgui.pop_item_width()
    # Show frame title:
    currentImageDescription = "Current image: " + currentImage.title
    if currentImage.frame:
        currentImageDescription += " originally frame " + str(currentImage.frame)
    imgui.text(currentImageDescription)
    # Show frame status:
    if prm.current_project.current_img.use:
        imgui.text("Frame status: include")
    else:
        imgui.text("Frame status: discard")
    # Show registration result
    _dx = currentImage.fulltransform[0][2]
    _dy = currentImage.fulltransform[1][2]
    imgui.text("Detected image shift (dx, dy) = ({:.2f}, {:.2f})".format(_dx, _dy))

    if not imgui.get_io().want_capture_keyboard:
        if Input.getKeyPressed(Input.KEY_2):
            prm.current_project.setFrameState(state = False)
        elif Input.getKeyPressed(Input.KEY_1):
            prm.current_project.setFrameState(state = True)
        if Input.getKeyPressed(Input.KEY_ARROW_LEFT):
            if Input.getKeyPressed(Input.KEY_LEFT_CTRL):
                Timeline_setFrame(cfg.current_frame - 10)
            else:
                Timeline_setFrame(cfg.current_frame - 1)
        elif Input.getKeyPressed(Input.KEY_ARROW_RIGHT):
            if Input.getKeyPressed(Input.KEY_LEFT_CTRL):
                Timeline_setFrame(cfg.current_frame + 10)
            else:
                Timeline_setFrame(cfg.current_frame + 1)
    if _showNewFrame:
        Timeline_setFrame(cfg.current_frame)
    imgui.end()

def Timeline_setFrame(f):
    f = min([prm.current_project.n_images-1, f])
    f = max([0, f])
    cfg.current_frame = f
    prm.current_project.setCurrentImage(cfg.current_frame)
    current_img = prm.current_project.current_img_data
    Renderer.BindImage(current_img)

def ImageRenderControls():
    windowWidth = imgui.get_window_content_region_width()
    imgui.begin("Visualization controls", flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
    # Histogram
    imgui.text("Contrast settings:")
    imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, *cfg.clr_fluorophore)
    imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM_HOVERED, *cfg.clr_fluorophore)
    imgui.plot_histogram("##histogram", cfg.histogram_yvals, graph_size = (cfg.histogram_view_width, cfg.histogram_view_height))
    imgui.pop_style_color(2)
    imgui.push_item_width(windowWidth - 170)
    _a, cfg.contrast_min = imgui.slider_int("min",cfg.contrast_min, 0, 10000)
    imgui.pop_item_width()
    imgui.same_line(spacing=20)
    _c, cfg.autocontrast = imgui.checkbox("auto", cfg.autocontrast)

    imgui.push_item_width(windowWidth - 170)
    _b, cfg.contrast_max = imgui.slider_int("max", cfg.contrast_max, 0, 10000)
    if _a or _b:
        cfg.autocontrast = False
    if _c and cfg.autocontrast:
        cfg.contrast_min = np.min(prm.current_project.current_img_data)
        cfg.contrast_max = np.max(prm.current_project.current_img_data)
    imgui.pop_item_width()
    imgui.same_line(spacing=20)
    cfg.clr_fluorophore = ColorSelector(cfg.clr_fluorophore, 20, 20)

    _, cfg.apply_registration_result = imgui.checkbox("apply registration result", cfg.apply_registration_result)
    imgui.end()

def ColorSelector(currentColor, width, height):
    x = imgui.get_cursor_pos_x()
    y = imgui.get_cursor_pos_y()
    pressed = imgui.core.color_button("##", currentColor[0], currentColor[1], currentColor[2], 1.0, 0.0, width, height)

    window_pos = imgui.get_window_position()
    # Pop up content
    popupPos = [window_pos.x + x - width, window_pos.y + y - height]
    imgui.set_next_window_position(popupPos[0], popupPos[1])
    if pressed:
        imgui.open_popup("colorpopup")
    if imgui.begin_popup("colorpopup"):
        _, color = imgui.color_edit3(" ", currentColor[0], currentColor[1], currentColor[2])
        imgui.end_popup()
        return color
    return currentColor