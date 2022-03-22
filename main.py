import GUIMain
import Input
import Reconstruction
import params as prm
import AnalysisMethods

def Start():
    GUIMain.Start()
    Input.Start()

def OnUpdate():
    retval = True
    Input.OnUpdate()
    AnalysisMethods.OnUpdate()
    _check = GUIMain.OnUpdate()
    retval = retval == _check
    return retval

def End():
    GUIMain.End()

if __name__ == '__main__':
    Start()
    running = True
    while running:
        running = OnUpdate()
    End()