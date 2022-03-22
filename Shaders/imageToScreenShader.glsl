#vertex
#version 420

layout(location = 0) in vec3 position;

out vec2 UV;
out vec2 fShift;
uniform mat4 mvpMat;
uniform int flipHorizontal;
uniform int flipVertical;

uniform float yShift;
uniform float xShift;
uniform float stackWidth;

void main()
{
    gl_Position = mvpMat * vec4(position, 1.0);
    UV = (vec2(position.x, position.y) + 1.0) / 2.0;
    UV.y -= 1 * yShift / stackWidth;
    UV.x += 1 * xShift / stackWidth;
    if (flipVertical == 1)
        UV.y = 1.0 - UV.y;
    if (flipHorizontal == 1)
        UV.x = 1.0 - UV.x;
    fShift = vec2(-xShift, -yShift) / stackWidth;
}


#fragment 
#version 420

layout(location = 0) out vec4 fragmentColor;
layout(binding = 0) uniform usampler2D inputImage;

in vec2 UV;
in vec2 fShift;

uniform float xMin;
uniform float xMax;
uniform float yMin;
uniform float yMax;

uniform vec3 color;
uniform float contrastMin;
uniform float contrastMax;
uniform int imageState;

void main()
{
    vec2 fUV = UV + fShift;
    float grayScale = float(texture(inputImage, UV).r);
    float contrast = (grayScale - contrastMin) / (contrastMax - contrastMin);
    contrast = max(0.0, contrast);
    float grayValue = clamp(contrast, 0.0, 1.0);
    float brightness = 1.0;
    fragmentColor = vec4(grayValue * color, 1.0);
    if ((fUV.x < xMin) || (fUV.x > xMax) || (fUV.y < yMin) || (fUV.y > yMax))
    {
        fragmentColor = vec4(grayValue * 0.8, grayValue * 0.8, grayValue * 0.8, 1.0);
    }
    if (imageState == 0)
    {
        fragmentColor = vec4(grayValue * 1.0, grayValue * 0.7, grayValue * 0.7, 1.0);
        float borderThickness = 0.01;
        if ((fUV.x < borderThickness) || (fUV.x > (1.0 - borderThickness)) || (fUV.y < borderThickness) || (fUV.y > (1.0 - borderThickness)))
        {
        fragmentColor = vec4(0.5, 0.0, 0.0, 1.0);
        }
    }
}
