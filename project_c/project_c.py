# Untitled - By: sjboy32 - Thu Jul 31 2025
import sensor, image, time
from pyb import UART

# 设置两个高电平触发的按键
uart = UART(3, 9# Untitled - By: boy - Thu Jul 31 2025
import sensor, image, time
from pyb import UART

# 设置两个高电平触发的按键
uart = UART(3, 9600)  # TX=P4, RX=P5 对应 UART3
uart.init(9600, bits=8, parity=None, stop=1)
# 相机初始化（所有工程共用）
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)
sensor.set_windowing((200, 240))
sensor.skip_frames(time=2000)
clock = time.clock()

# 常量
CENTER_X = 100
CENTER_Y = 120
FRAME_WIDTH_MM = 176
FRAME_HIGHT_MM = 265
DISTANCE_MM_2 = 1400
FRAME_WIDTH_PIXEL_2 = 80
FRAME_HEIGHT_PIXEL_2 = 120

def find_center_min_blob(blobs):
    blob = None
    min_area = 100000
    for b in blobs:
        if abs(b.cx() - CENTER_X) + abs(b.cy() - CENTER_Y) > 50:
            continue
        if b.area() > min_area:
            continue
        blob = b
        min_area = b.area()
    return blob

def find_center_max_blob(blobs):
    blob = None
    max_area = 0
    for b in blobs:
        if abs(b.cx() - CENTER_X) + abs(b.cy() - CENTER_Y) > 50:
            continue
        if b.area() < max_area:
            continue
        blob = b
        max_area = b.area()
    return blob

def project_1():
    img = sensor.snapshot()
    frames = img.find_blobs([(150, 255)])
    frame_blob = find_center_min_blob(frames)
    if not frame_blob:
        print("NO FRAME")
        return

    roi_x = frame_blob.x() + 2
    roi_y = frame_blob.y() + 2
    roi_w = frame_blob.w() - 4
    roi_h = frame_blob.h() - 4

    step = 5
    black_threshold = 10

    # 行扫描
    min_row_black = 99999
    min_row_y = -1
    for y in range(roi_y, roi_y + roi_h, step):
        black_count = 0
        for x in range(roi_x, roi_x + roi_w):
            if img.get_pixel(x, y) < 100:
                black_count += 1
        if black_threshold < black_count < min_row_black:
            min_row_black = black_count
            min_row_y = y

    # 列扫描
    min_col_black = 99999
    min_col_x = -1
    for x in range(roi_x, roi_x + roi_w, step):
        black_count = 0
        for y in range(roi_y, roi_y + roi_h):
            if img.get_pixel(x, y) < 100:
                black_count += 1
        if black_threshold < black_count < min_col_black:
            min_col_black = black_count
            min_col_x = x

    print("最少有效黑色行：Y =", min_row_y, ", 黑色像素 =", min_row_black)
    print("最少有效黑色列：X =", min_col_x, ", 黑色像素 =", min_col_black)

    img.draw_rectangle(frame_blob.rect())
    if min_row_y != -1:
        img.draw_line(roi_x, min_row_y, roi_x + roi_w, min_row_y, color=0)
    if min_col_x != -1:
        img.draw_line(min_col_x, roi_y, min_col_x, roi_y + roi_h, color=0)

def project_2():
    img = sensor.snapshot()
    frames = img.find_blobs([(150, 255)])
    frame_blob = find_center_min_blob(frames)
    if not frame_blob:
        print("NO FRAME")
        return

    distance = DISTANCE_MM_2 * FRAME_HEIGHT_PIXEL_2 / frame_blob.h()
    frame_roi = (frame_blob.x()+5, frame_blob.y()+5, frame_blob.w()-10, frame_blob.h()-10)
    if frame_roi[2] <= 0 or frame_roi[3] <= 0:
        print("ROI ERROR")
        return

    objs = img.find_blobs([(0, 150)], roi=frame_roi)
    obj_blob = find_center_max_blob(objs)
    if not obj_blob:
        print("NO OBJS")
        return

    obj_w_mm = obj_blob.w() / frame_blob.w() * FRAME_WIDTH_MM
    density = obj_blob.density()

    print("宽度像素:", frame_blob.w(), "高度像素:", frame_blob.h())
    if density > 0.9:
        print("矩形")
    elif density > 0.6:
        print("圆形")
    elif density > 0.4:
        print("三角形")
    else:
        print("无法识别形状")

    img.draw_string(10, 10, "length:" + str(obj_w_mm) + "mm")
    img.draw_string(10, 20, "distance:" + str(distance) + "mm")
    img.draw_rectangle(frame_blob.rect())
    img.draw_rectangle(obj_blob.rect())

# 主循环，检查按键并执行对应工程
current_project = 0  # 0 表示无任务，1 表示执行project_1，2 表示执行project_2

while True:
    clock.tick()
    if uart.any():  # 检查是否有串口数据
        data = uart.read().decode().strip()
        print("接收到串口数据：", data)
    # 按键设置工程编号
    if data == '1':
        current_project = 1
        print("\n>>> 切换至工程1：黑色像素分析")
    elif data == '2':
        current_project = 2
        print("\n>>> 切换至工程2：形状与距离识别")

    # 根据当前标志位执行对应工程
    if current_project == 1:
        project_1()
        current_project = 0  # 任务完成后重置
    elif current_project == 2:
        project_2()
        current_project = 0  # 任务完成后重置
