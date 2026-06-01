# #roi裁剪工具
# import cv2
# import numpy as np
# import os
#
# # ================= 1. 你的标记数据 =================
# # 直接把坐标放进数组里
# lines_data = [
#     [298, 1254, 5164, 1202],
#     [302, 1542, 5164, 1490],
#     [298, 1844, 5168, 1785],
#     [302, 2154, 5172, 2095],
#     [313, 2457, 5179, 2398],
#     [317, 2755, 5187, 2700],
#     [291, 1239, 317, 2759],
#     [5161, 1180, 5190, 2704],
#     [596, 1242, 622, 2747],
#     [903, 1243, 918, 2744],
#     [1202, 1243, 1221, 2744],
#     [1508, 1228, 1531, 2733],
#     [1818, 1232, 1833, 2730],
#     [2128, 1232, 2143, 2733],
#     [2438, 1217, 2449, 2722],
#     [2737, 1224, 2759, 2715],
#     [3039, 1221, 3073, 2718],
#     [3346, 1210, 3383, 2700],
#     [3659, 1210, 3681, 2715],
#     [3977, 1206, 3988, 2707],
#     [4264, 1210, 4294, 2711],
#     [4578, 1210, 4585, 2704],
#     [4873, 1195, 4888, 2685]
# ]
#
# img_path = r"E:\framePiccamindex0\20260429\ASL260213A480401.Jpeg"
# # 输出文件夹，自动建在原图同一个目录下
# output_dir = r"D:\Users\18703\Desktop\22"
#
#
# # ================= 2. 核心处理逻辑 =================
#
# def get_intersection(line1, line2):
#     """计算两条直线的交点"""
#     x1, y1, x2, y2 = line1
#     x3, y3, x4, y4 = line2
#
#     # 使用行列式计算交点
#     denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
#     if denom == 0:
#         return None  # 平行
#
#     px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
#     py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
#     return (int(px), int(py))
#
#
# def main():
#     # 读取图像
#     img = cv2.imread(img_path)
#     if img is None:
#         print(f"❌ 找不到图像，请检查路径是否正确: {img_path}")
#         return
#
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#
#     # 1. 区分横线和竖线
#     h_lines = []
#     v_lines = []
#     for line in lines_data:
#         x1, y1, x2, y2 = line
#         # 如果 X跨度 > Y跨度，说明是横线
#         if abs(x2 - x1) > abs(y2 - y1):
#             h_lines.append(line)
#         else:
#             v_lines.append(line)
#
#     # 2. 排序：横线按Y坐标从上到下排，竖线按X坐标从左到右排
#     h_lines.sort(key=lambda l: (l[1] + l[3]) / 2)
#     v_lines.sort(key=lambda l: (l[0] + l[2]) / 2)
#
#     print(f"✅ 识别到 {len(h_lines)} 条横线, {len(v_lines)} 条竖线")
#
#     # 3. 计算所有网格的交点网格矩阵
#     grid_points = []
#     for h_line in h_lines:
#         row_points = []
#         for v_line in v_lines:
#             pt = get_intersection(h_line, v_line)
#             row_points.append(pt)
#         grid_points.append(row_points)
#
#     # 4. 根据交点，遍历切割并保存每一个 ROI
#     rows = len(h_lines) - 1
#     cols = len(v_lines) - 1
#     count = 0
#
#     for r in range(rows):
#         for c in range(cols):
#             # 获取该方格的4个顶点
#             tl = grid_points[r][c]  # 左上
#             tr = grid_points[r][c + 1]  # 右上
#             bl = grid_points[r + 1][c]  # 左下
#             br = grid_points[r + 1][c + 1]  # 右下
#
#             # 获取包含这4个点的正规矩形外框 (Bounding Box)
#             x_min = min(tl[0], tr[0], bl[0], br[0])
#             x_max = max(tl[0], tr[0], bl[0], br[0])
#             y_min = min(tl[1], tr[1], bl[1], br[1])
#             y_max = max(tl[1], tr[1], bl[1], br[1])
#
#             # 防止越界
#             x_min = max(0, x_min)
#             y_min = max(0, y_min)
#             x_max = min(img.shape[1], x_max)
#             y_max = min(img.shape[0], y_max)
#
#             # 裁剪图像
#             roi_img = img[y_min:y_max, x_min:x_max]
#
#             # 命名格式：Row_Col.jpg (例如 R1_C1.jpg)
#             save_name = f"R{r + 1}_C{c + 1}.jpg"
#             save_path = os.path.join(output_dir, save_name)
#
#             cv2.imwrite(save_path, roi_img)
#             count += 1
#
#     print(f"🎉 裁剪完成！成功保存了 {count} 个芯片图像块。")
#     print(f"📁 图像保存在: {output_dir}")
#
#
# if __name__ == "__main__":
#     main()

import cv2
import numpy as np
import os
from PIL import Image  # 引入 Pillow 解决 OpenCV 无法解析超大图的问题

# 解除 Pillow 默认的像素限制保护
Image.MAX_IMAGE_PIXELS = None

# ================= 1. 你发来的全新 22 条巨型长图标记数据 =================
lines_data = [
    # 17 条横线坐标 (自动分类)
    [2466, 3733, 12285, 3778],
    [2431, 5938, 12273, 5983],
    [2452, 8065, 12328, 8088],
    [2474, 10180, 12317, 10247],
    [2486, 12362, 12328, 12396],
    [2497, 14522, 12362, 14522],
    [2400, 16644, 12375, 16684],
    [2498, 18769, 12395, 18809],
    [2360, 20933, 12454, 20992],
    [2439, 23137, 12375, 23098],
    [2439, 25242, 12493, 25242],
    [2441, 27369, 12497, 27402],
    [2452, 29540, 12531, 29562],
    [2419, 38136, 12625, 38149],
    [2483, 35950, 12574, 36027],
    [2457, 33828, 12587, 33880],
    [2419, 31694, 12574, 31707],

    # 5 条竖线坐标 (自动分类)
    [2366, 3640, 2457, 37999],
    [4907, 3680, 5065, 38227],
    [7320, 3601, 7558, 38187],
    [9774, 3601, 10051, 38108],
    [12307, 3680, 12584, 38148]
]

# 已经更新为你的最新长图路径
img_path = r"D:\Users\18703\Desktop\xout\3\N59L634100215536900896_STD-324_N59L634100211804_20260521164912_84ASA01082D001.jpg"
output_dir = r"D:\Users\18703\Desktop\xout\out"


# ================= 2. 核心数学与分块处理逻辑 =================

def get_intersection(line1, line2):
    """ 计算两条直线的精确交点 """
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if denom == 0:
        return None  # 平行线无交点

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (int(px), int(py))


def main():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 自动提取不带后缀的原图片名称
    base_name = os.path.splitext(os.path.basename(img_path))[0]

    # 1. 自动高精度区分横线和竖线
    h_lines = []
    v_lines = []
    for line in lines_data:
        x1, y1, x2, y2 = line
        if abs(x2 - x1) > abs(y2 - y1):
            h_lines.append(line)
        else:
            v_lines.append(line)

    # 2. 拓扑位置排序：横线自上而下，竖线自左而右
    h_lines.sort(key=lambda l: (l[1] + l[3]) / 2)
    v_lines.sort(key=lambda l: (l[0] + l[2]) / 2)

    print(f"📊 数据清洗成功：检测到 {len(h_lines)} 条边界横线，{len(v_lines)} 条边界竖线。")

    if len(h_lines) < 2 or len(v_lines) < 2:
        print("❌ 错误：线段数量不足以构成闭合的切片网格，请检查输入！")
        return

    # 3. 矩阵化交点网格
    grid_points = []
    for h_line in h_lines:
        row_points = []
        for v_line in v_lines:
            pt = get_intersection(h_line, v_line)
            row_points.append(pt)
        grid_points.append(row_points)

    # 4. 用 Pillow 绕过 OpenCV 的大图拦截限制
    try:
        print("⏳ 正在通过 Pillow 核心挂载大图（指针常驻，不吃内存）...")
        pil_img = Image.open(img_path)
        img_width, img_height = pil_img.size
        print(f"🚀 长图尺寸捕获成功: W={img_width}, H={img_height}，正在启动安全裁剪内核...")
    except Exception as e:
        print(f"❌ 无法读取图像，请确认路径或文件是否损坏: {img_path}\n原因: {e}")
        return

    rows = len(h_lines) - 1
    cols = len(v_lines) - 1
    count = 0

    for r in range(rows):
        for c in range(cols):
            # 获取当前方格的4个多边形交点
            tl = grid_points[r][c]      # 左上
            tr = grid_points[r][c + 1]  # 右上
            bl = grid_points[r + 1][c]  # 左下
            br = grid_points[r + 1][c + 1]  # 右下

            if not all([tl, tr, bl, br]):
                continue

            # 计算外接矩形框边界
            x_min = min(tl[0], tr[0], bl[0], br[0])
            x_max = max(tl[0], tr[0], bl[0], br[0])
            y_min = min(tl[1], tr[1], bl[1], br[1])
            y_max = max(tl[1], tr[1], bl[1], br[1])

            # 严格防越界限幅
            x_min = max(0, x_min)
            y_min = max(0, y_min)
            x_max = min(img_width, x_max)
            y_max = min(img_height, y_max)

            if (x_max <= x_min) or (y_max <= y_min):
                continue

            # 指针级局部无损裁剪
            crop_box = (x_min, y_min, x_max, y_max)
            roi_pil = pil_img.crop(crop_box)

            # 将裁剪完的局部图像块转为 OpenCV 格式进行高效存储
            roi_img = cv2.cvtColor(np.array(roi_pil), cv2.COLOR_RGB2BGR)

            # 保持你的命名规范：原图片名字 + _R行_C列.jpg
            save_name = f"{base_name}_R{r + 1}_C{c + 1}.jpg"
            save_path = os.path.join(output_dir, save_name)

            cv2.imwrite(save_path, roi_img)
            count += 1
            print(f" ╰─> 已成功保存子晶圆块: {save_name}")

    print(f"\n🎉 完美搞定！所有网格芯片区域已裁剪完毕。")
    print(f"📁 成功输出了 {count} 个包含原图命名的子ROI，请前往查看： {output_dir}")


if __name__ == "__main__":
    main()