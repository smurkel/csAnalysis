# appdata
window_name = "csAnalysis"
window_width = 1280
window_height = 870
fullscreen = False
# misc values
frametime = 100
# input
doubleClickInterval = 30
# renderer
screenView_pan_correctionFactor = 0.95
screenView_zoom = 1.0
screenView_base_zoom = 0.71
screenView_xRange = [318, 1549]
screenView_yRange = [321, 1060]
screenView_xCenter = -390
screenView_yCenter = 189
screenView_base_xOffset = 53
screenView_base_yOffset = -300
screenView_translation_ndcPerPixel = 1
screenView_flipHorizontal = False
screenView_flipVertical = True
screenView_translate_speed = 2 # turns out to align when this value is 2. easy!
screenView_zoom_speed_smooth = 0.02
screenView_zoom_speed_discrete = 0.24
screenView_zoom_smoothStop_decayrate = 0.07
# image viewer
clr_fluorophore = (1.0, 1.0, 1.0)
autocontrast = True
contrast_min = 100
contrast_max = 5000
current_frame = 0
timeline_focus_magnification = 20
apply_registration_result = True
histogram_yvals = None
histogram_bin_edges = None
histogram_n_bins = "auto"
histogram_view_width = 320
histogram_view_height = 40
# analysis menus
active_menu = "Project settings"
# selection
selection_filter = ""
selection_filter_options = ["Discard", "Keep", "Keep and discard rest"]
selection_combo_width = 169
selection_selected_option = 0
selection_apply_button_width = 40
selection_apply_button_height = 20
selection_range = (0, 1)
selection_selected_option_range = 0
selection_bake_button_width = 190
selection_bake_button_height = 25
# registration
registration_matching_options = ["All to first", "Each to previous", "All to selected frame"]
registration_matching_selected_option = 0
registration_matching_selected_frame = 0
registration_start_button_width = 190
registration_start_button_height = 20
registration_running = False
registration_imgs_to_reg_total = 1
registration_imgs_registered = 0
registration_parallel_processes = 10
# filtering
fltr_options = ["None", "Difference", "Subtract activation frame"]
fltr_selected = 0
fltr_applied = 0
fltr_negative_options = ["Zero", "Absolute value", "None"]
fltr_neg_selected = 0
fltr_neg_offset = 500
fltr_combo_width = 160
# colours
debu1 = 100
clr_stage_stackpreparation = (24 / 255, 80 / 255, 60 / 255)
clr_stage_misc = (80 / 255, 60 / 255, 24 / 255)
clr_stage_default  = (30 / 255, 56 / 255, 87 / 255)
clr_disabled_text = (0.7, 0.7, 0.7)
clr_disabled = (50 / 255, 50 / 255, 50 / 255)
clr_fstate_use = (0.2, 0.8, 0.2, 1.0)
clr_fstate_discard = (0.8, 0.2, 0.2, 1.0)