# 拼图用固定格式5*16
import cv2
import numpy as np
import os

# ================= 1. 配置参数 =================
# 存放 80 张小图的文件夹路径
input_dir = r"D:\Users\18703\Desktop\22\ok"

# 拼接后输出的大图路径 (使用 .png 保证无损画质)
output_path = r"D:\Users\18703\Desktop\22\Stitched_Full_Image.png"

# 网格的行数和列数
ROWS = 5
COLS = 16


# ================= 2. 核心拼接逻辑 =================
def stitch_images():
    print(f"🚀 开始读取 {ROWS} 行 {COLS} 列的图像碎块...")

    images_dict = {}

    # 1. 读取所有图片并存入字典
    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            filename = f"R{r}_C{c}.jpg"
            filepath = os.path.join(input_dir, filename)

            if not os.path.exists(filepath):
                print(f"❌ 错误: 找不到文件 {filepath}！请确保所有 80 张图都在该文件夹下。")
                return

            img = cv2.imread(filepath)
            if img is None:
                print(f"❌ 错误: 无法读取图像文件 {filepath}")
                return

            images_dict[(r, c)] = img

    # 2. 计算每一行的最大高度，和每一列的最大宽度
    # 这样就算你切图时有些图大了一两像素，也不会报错变形
    row_heights = [0] * ROWS
    col_widths = [0] * COLS

    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            h, w = images_dict[(r, c)].shape[:2]
            if h > row_heights[r - 1]:
                row_heights[r - 1] = h
            if w > col_widths[c - 1]:
                col_widths[c - 1] = w

    # 3. 计算最终大图的整体分辨率
    total_height = sum(row_heights)
    total_width = sum(col_widths)
    print(f"📏 计算得出拼接后的大图分辨率将为: {total_width} x {total_height}")

    # 4. 创建纯黑背景的空白画布 (3通道 RGB，无损格式)
    canvas = np.zeros((total_height, total_width, 3), dtype=np.uint8)

    print("🧩 正在执行像素级精准拼接...")

    # 5. 将每一块小图贴入画布的精确坐标中
    current_y = 0
    for r in range(1, ROWS + 1):
        current_x = 0
        for c in range(1, COLS + 1):
            img = images_dict[(r, c)]
            h, w = img.shape[:2]

            # 将小图写入画布对应区域
            canvas[current_y: current_y + h, current_x: current_x + w] = img

            # X 坐标向右移动当前列的最大宽度
            current_x += col_widths[c - 1]

        # Y 坐标向下移动当前行的最大高度
        current_y += row_heights[r - 1]

    # 6. 保存无损大图 (PNG 格式天然无损压缩)
    print("💾 正在保存无损大图 (文件可能较大，请稍候)...")
    cv2.imwrite(output_path, canvas)

    print(f"\n🎉 拼接完美结束！")
    print(f"🖼️ 无损大图已保存至: {output_path}")


if __name__ == "__main__":
    stitch_images()