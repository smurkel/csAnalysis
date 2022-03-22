from OpenGLClasses import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import config as cfg
import params as prm

imgTexture = None
channelShader = None
screenShader = None
vertexArray = None

def Init():
    global screenShader, channelShader, vertexArray, FBO_A, FBO_B, screenViewVertexArray, imgTexture, timelineTexture
    imgTexture = Texture()
    screenShader = Shader("C:/Users/mgflast/PycharmProjects/csAnalysis/Shaders/imageToScreenShader.glsl")
    vertices = [-1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0, 1.0, 1.0]
    indices = [0, 1, 2, 2, 0, 3]
    vertexBuffer = VertexBuffer(vertices)
    indexBuffer = IndexBuffer(indices)
    vertexArray = VertexArray(vertexBuffer, indexBuffer)

def RecompileShader():
    global screenShader
    screenShader = Shader("C:/Users/mgflast/PycharmProjects/csAnalysis/Shaders/imageToScreenShader.glsl")

def BindImage(img):
    global imgTexture
    cfg.histogram_yvals, cfg.histogram_bin_edges = np.histogram(img, cfg.histogram_n_bins)
    cfg.histogram_yvals = cfg.histogram_yvals.astype('float32')
    imgTexture.update(img)
    if cfg.autocontrast:
        cfg.contrast_min = np.min(img)
        cfg.contrast_max = np.max(img)

def BindTimelineImage(img):
    global timelineTexture
    timelineTexture.update(img)


def Render():
    # Bind VAO
    vertexArray.bind()
    # Bind shader and upload uniforms
    screenShader.bind()
    screenShader.uniform1f("xMin", prm.current_project.roi[0] / prm.current_project.width)
    screenShader.uniform1f("xMax", prm.current_project.roi[2] / prm.current_project.height)
    screenShader.uniform1f("yMin", prm.current_project.roi[1] / prm.current_project.width)
    screenShader.uniform1f("yMax", prm.current_project.roi[3] / prm.current_project.height)
    screenShader.uniform1i("flipHorizontal", cfg.screenView_flipHorizontal)
    screenShader.uniform1i("flipVertical", cfg.screenView_flipVertical)
    screenShader.uniform1f("contrastMin", cfg.contrast_min)
    screenShader.uniform1f("contrastMax", cfg.contrast_max)
    screenShader.uniform1i("imageState", int(prm.current_project.current_img.use))
    if cfg.apply_registration_result:
        screenShader.uniform1f("xShift", prm.current_project.current_img.fulltransform[0][2])
        screenShader.uniform1f("yShift", prm.current_project.current_img.fulltransform[1][2])
    else:
        screenShader.uniform1f("xShift", 0.0)
        screenShader.uniform1f("yShift", 0.0)
    screenShader.uniform1f("stackWidth", prm.stackwidth)
    screenShader.uniform3f("color", cfg.clr_fluorophore)
    mvpMat = MVP_Matrix()
    screenShader.uniformmat4("mvpMat", mvpMat)
    imgTexture.bind(0)
    glDrawElements(GL_TRIANGLES, vertexArray.indexBuffer.getCount(), GL_UNSIGNED_SHORT, None)
    screenShader.unbind()
    vertexArray.unbind()
    glActiveTexture(GL_TEXTURE0)

def MVP_Matrix():
    # Calculate the model, view, and projection matrices.
    # Model:
    totalZoom = cfg.screenView_base_zoom * cfg.screenView_zoom
    scaleMat = np.matrix([[totalZoom * 1000.0, 0.0, 0.0, 0.0],[0.0, totalZoom * 1000.0, 0.0, 0.0],[0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
    translationMat = np.matrix([[1.0, 0.0, 0.0, -(cfg.screenView_xCenter + cfg.screenView_base_xOffset) * cfg.screenView_translation_ndcPerPixel],[0.0, 1.0, 0.0, -(cfg.screenView_yCenter + cfg.screenView_base_yOffset) * cfg.screenView_translation_ndcPerPixel],[0.0, 0.0, 1.0, 0.0],[0.0, 0.0, 0.0, 1.0]])
    modelMat = np.matmul(translationMat, scaleMat)
    # View:
    # skipping view matrix as it would be identity anyway.
    # Projection:
    def _orthographicMatrix(l, r, b, t, n, f):
        dx = r - l
        dy = t - b
        dz = f - n
        rx = -(r + l) / (r - l)
        ry = -(t + b) / (t - b)
        rz = -(f + n) / (f - n)
        return np.matrix([[2.0 / dx, 0, 0, rx],
                          [0, 2.0 / dy, 0, ry],
                          [0, 0, -2.0 / dz, rz],
                          [0, 0, 0, 1]])

    projectionMat = _orthographicMatrix(-cfg.window_width, cfg.window_width, -cfg.window_height, cfg.window_height, -100, 100)
    return np.matmul(projectionMat, modelMat)