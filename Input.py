import glfw
import params as prm
import config as cfg

cursorPos = [0.0, 0.0]
cursorOffset = [0.0, 0.0]
scrollOffset = [0.0, 0.0]

KEY_LEFT_SHIFT = glfw.KEY_LEFT_SHIFT
KEY_LEFT_CTRL = glfw.KEY_LEFT_CONTROL
KEY_DELETE = glfw.KEY_DELETE
KEY_SPACE = glfw.KEY_SPACE
KEY_S = glfw.KEY_S
KEY_A = glfw.KEY_A
KEY_P = glfw.KEY_P
KEY_ARROW_LEFT = glfw.KEY_LEFT
KEY_ARROW_RIGHT = glfw.KEY_RIGHT
KEY_ESCAPE = glfw.KEY_ESCAPE
KEY_1 = glfw.KEY_1
KEY_2 = glfw.KEY_2

doubleClickTimer = 0.0
doubleClickPossible = False
memTime = None

def Start():
    global memTime
    window = prm.m_window
    glfw.set_scroll_callback(window, scrollCallback)
    memTime = glfw.get_time()

def OnUpdate():
    global cursorPos, cursorOffset, scrollOffset, buttonPressReset, memTime, doubleClickTimer, doubleClickPossible
    ## update time
    scrollOffset = [0, 0]
    newTime = glfw.get_time()
    prm.dt = newTime - memTime
    memTime = newTime
    # Get new events
    glfw.poll_events()
    newCursorPos = getMousePosition()
    cursorOffset = [newCursorPos[0] - cursorPos[0], newCursorPos[1] - cursorPos[1]]
    cursorPos = newCursorPos
    if getMousePressed(0) and not doubleClickPossible:
        doubleClickTimer = cfg.doubleClickInterval
    if not doubleClickPossible and not getMousePressed(0):
        if doubleClickTimer > 0.0:
            doubleClickPossible = True
    if doubleClickTimer < 0.0:
        doubleClickPossible = False
    doubleClickTimer -= prm.dt

def getDoubleClick():
    global timeSinceLastMouseRelease, doubleClickPossible
    if doubleClickPossible:
        if getMousePressed(0):
            doubleClickPossible = False
            return True
    return False

def getMousePressed(button):
    """Returns True is the selected button is pressed (can be pressed for many frames)"""
    state = glfw.get_mouse_button(prm.m_window, button)
    if state == glfw.PRESS:
        return True
    return False

def getMouseReleased(button):
    """Returns True is the button was clicked and is no longer clicked (returns True in only 1 frame)"""
    state = glfw.get_mouse_button(prm.m_window, button)
    if state == glfw.RELEASE:
        return True
    return False

def getMousePosition():
    position = glfw.get_cursor_pos(prm.m_window)
    return position

def scrollCallback(window, scrollx, scrolly):
    global scrollOffset
    scrolledInThisFrame = True
    scrollOffset = [scrollx, scrolly]

def getKeyPressed(button):
    """Button must be one of Input.KEYCODE - see definitions in Input.py"""
    return glfw.get_key(prm.m_window, button)
