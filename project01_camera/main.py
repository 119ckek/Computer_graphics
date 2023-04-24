from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np
# shader.py
import shader as sh

# GRID_NUM is number of xz plane grid
GRID_NUM = (1 << 7)
# GRID_LEN is length of grid
GRID_LEN = 100
# limit of camera elevation angle
CAM_ELV_MAX = np.radians(360)
CAM_ELV_MIN = np.radians(0)
# limit of camera radius
CAM_RAD_MAX = 5.
CAM_RAD_MIN = .1

# g_button_hold is button hold flag
g_l_button_hold = False
g_r_button_hold = False
# previous cursor position
g_prev_xpos = 0
g_prev_ypos = 0
# camera azimuth and elevation and radius
g_cam_azm = 0.
g_cam_elv = 0.
g_cam_rad = 1.
# target point
g_target = glm.vec3(0, 0, 0)
# projection mode 0 is orthogonal, 1 is perspective
g_P_mode = 1
# up vector
g_up_vector = glm.vec3(0, 1, 0)
# pan vector about camera frame
g_pan = glm.vec3(0, 0, 0)

def key_callback(window, key, scancode, action, mods):
    global g_P_mode
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE)
    elif key == GLFW_KEY_V and action == GLFW_PRESS:
        # switch projection mode 0 to 1 or 1 to 0
        g_P_mode = (g_P_mode + 1) % 2

# detect button hold status
def button_callback(window, button, action, mod):
    global g_l_button_hold, g_r_button_hold
    if button == GLFW_MOUSE_BUTTON_LEFT:
        if action == GLFW_PRESS:
            g_l_button_hold = True
        elif action == GLFW_RELEASE:
            g_l_button_hold = False
    elif button == GLFW_MOUSE_BUTTON_RIGHT:
        if action == GLFW_PRESS:
            g_r_button_hold = True
        elif action == GLFW_RELEASE:
            g_r_button_hold = False

def cursor_callback(window, xpos, ypos):
    global g_l_button_hold, g_r_button_hold
    global g_prev_xpos, g_prev_ypos
    global g_cam_azm, g_cam_elv, g_target
    
    # offset of cursor position
    dxpos = xpos - g_prev_xpos
    dypos = ypos - g_prev_ypos

    if g_l_button_hold == True:
        # when upvector.y is negative, the azimuth angle direction differs. so multiplied g_up_vector[1].
        g_cam_azm += -g_up_vector[1] * np.radians(dxpos) / 5
        g_cam_elv += np.radians(dypos) / 5

        # limit g_cam_elv range 0 to 2*PI radians.
        if g_cam_elv > CAM_ELV_MAX:
            g_cam_elv -= CAM_ELV_MAX
        elif g_cam_elv < CAM_ELV_MIN:
            g_cam_elv += CAM_ELV_MAX

        # in the case of upside-down, upvector.y must be fliped.
        if np.radians(90) < g_cam_elv and g_cam_elv < np.radians(270):
            g_up_vector[1] = -1
        else:
            g_up_vector[1] = 1
    elif g_r_button_hold == True:
        # pan u,v direction
        g_pan[0] += .005 * dxpos
        g_pan[1] += -.005 * dypos
    
    # renew prev_pos
    g_prev_xpos = xpos
    g_prev_ypos = ypos

def scroll_callback(window, xoffset, yoffset):
    global g_cam_rad

    next_rad = g_cam_rad - .1 * yoffset
    if CAM_RAD_MIN < next_rad and next_rad < CAM_RAD_MAX:
        g_cam_rad = next_rad

def prepare_vao_xzplane():
    # line vertexes list
    tempList = []
    for i in range(-GRID_NUM, GRID_NUM):
        # pararell to x-axis
        tempList.extend([GRID_LEN, 0, i / 10]) # v1
        if i % 5 == 0:
            tempList.extend([1, 1, 1])
        else:
            tempList.extend([.5, .5, .5])
        tempList.extend([-GRID_LEN, 0, i / 10]) # v2
        if i % 5 == 0:
            tempList.extend([1, 1, 1])
        else:
            tempList.extend([.5, .5, .5])
        # pararell to z-axis
        tempList.extend([i / 10, 0, GRID_LEN]) # v1
        if i % 5 == 0:
            tempList.extend([1, 1, 1])
        else:
            tempList.extend([.5, .5, .5])
        tempList.extend([i / 10, 0, -GRID_LEN]) # v2
        if i % 5 == 0:
            tempList.extend([1, 1, 1])
        else:
            tempList.extend([.5, .5, .5])
    
    vertices = (ctypes.c_float * len(tempList))(*tempList)

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    # python list to vertex data, glBufferData() overload
    glBufferData(GL_ARRAY_BUFFER, vertices, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

def prepare_vao_cube():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
        # position            color
        -0.3 ,  0.3 ,  0.3 ,  1, 0, 0, # v0
         0.3 , -0.3 ,  0.3 ,  1, 0, 0, # v2
         0.3 ,  0.3 ,  0.3 ,  1, 0, 0, # v1
                    
        -0.3 ,  0.3 ,  0.3 ,  0, 1, 0, # v0
        -0.3 , -0.3 ,  0.3 ,  0, 1, 0, # v3
         0.3 , -0.3 ,  0.3 ,  0, 1, 0, # v2
                    
        -0.3 ,  0.3 , -0.3 ,  0, 0, 1, # v4
         0.3 ,  0.3 , -0.3 ,  0, 0, 1, # v5
         0.3 , -0.3 , -0.3 ,  0, 0, 1, # v6
                    
        -0.3 ,  0.3 , -0.3 ,  0, 1, 1, # v4
         0.3 , -0.3 , -0.3 ,  0, 1, 1, # v6
        -0.3 , -0.3 , -0.3 ,  0, 1, 1, # v7
                    
        -0.3 ,  0.3 ,  0.3 ,  1, 0, 1, # v0
         0.3 ,  0.3 ,  0.3 ,  1, 0, 1, # v1
         0.3 ,  0.3 , -0.3 ,  1, 0, 1, # v5
                    
        -0.3 ,  0.3 ,  0.3 ,  1, 1, 0, # v0
         0.3 ,  0.3 , -0.3 ,  1, 1, 0, # v5
        -0.3 ,  0.3 , -0.3 ,  1, 1, 0, # v4
 
        -0.3 , -0.3 ,  0.3 ,  0, .5, 0, # v3
         0.3 , -0.3 , -0.3 ,  0, .5, 0, # v6
         0.3 , -0.3 ,  0.3 ,  0, .5, 0, # v2
                    
        -0.3 , -0.3 ,  0.3 ,  0, 0, .5, # v3
        -0.3 , -0.3 , -0.3 ,  0, 0, .5, # v7
         0.3 , -0.3 , -0.3 ,  0, 0, .5, # v6
                    
         0.3 ,  0.3 ,  0.3 ,  .5, 0, 0, # v1
         0.3 , -0.3 ,  0.3 ,  .5, 0, 0, # v2
         0.3 , -0.3 , -0.3 ,  .5, 0, 0, # v6
                    
         0.3 ,  0.3 ,  0.3 ,  .5, 0, .5, # v1
         0.3 , -0.3 , -0.3 ,  .5, 0, .5, # v6
         0.3 ,  0.3 , -0.3 ,  .5, 0, .5, # v5
                    
        -0.3 ,  0.3 ,  0.3 ,  .5, .5, 0, # v0
        -0.3 , -0.3 , -0.3 ,  .5, .5, 0, # v7
        -0.3 , -0.3 ,  0.3 ,  .5, .5, 0, # v3
                    
        -0.3 ,  0.3 ,  0.3 ,  0, .5, .5, # v0
        -0.3 ,  0.3 , -0.3 ,  0, .5, .5, # v4
        -0.3 , -0.3 , -0.3 ,  0, .5, .5, # v7
    )

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)      # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)   # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr, GL_STATIC_DRAW) # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), ctypes.c_void_p(3*glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO


def main():
    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)   # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE) # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(800, 800, '2019088722_박지원', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback)
    glfwSetMouseButtonCallback(window, button_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetCursorPosCallback(window, cursor_callback)

    # load shaders
    shader_program = sh.load_shaders(sh.g_vertex_shader_src, sh.g_fragment_shader_src)

    # get uniform locations
    M_loc = glGetUniformLocation(shader_program, 'M')
    
    # prepare vaos
    vao_xzplane = prepare_vao_xzplane()
    vao_cube = prepare_vao_cube()

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glUseProgram(shader_program)

        # projection matrix
        P = glm.mat4()
        if g_P_mode == 0:
            P = glm.ortho(-2, 2, -2, 2, -2, 2)
        elif g_P_mode == 1:
            P = glm.perspective(45, 1, 1, 10)

        # set camera point offset from target point
        cam_x = g_cam_rad * np.cos(g_cam_elv) * np.sin(g_cam_azm)
        cam_y = g_cam_rad * np.sin(g_cam_elv)
        cam_z = g_cam_rad * np.cos(g_cam_elv) * np.cos(g_cam_azm)

        # view matrix
        V = glm.lookAt(glm.vec3(cam_x, cam_y, cam_z) + g_target, g_target, g_up_vector)
        # translate origin point
        V[3][0] += g_pan[0]
        V[3][1] += g_pan[1]

        # current frame: P*V*I (now this is the world frame)
        I = glm.mat4()
        MVP = P * V * I
        glUniformMatrix4fv(M_loc, 1, GL_FALSE, glm.value_ptr(MVP))

        # draw objects
        glBindVertexArray(vao_xzplane)
        glDrawArrays(GL_LINES, 0, 8 * GRID_NUM)

        glBindVertexArray(vao_cube)
        glDrawArrays(GL_TRIANGLES, 0, 36)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

    # terminate glfw
    glfwTerminate()

if __name__ == "__main__":
    main()
