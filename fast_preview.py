import bpy
import math
from pathlib import Path

# 1. Очистка сцены
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

BASE_DIR = Path("D:/project/python/dragon")
OBJ_PATH = BASE_DIR / "dragon3d.obj"
OUT_VIDEO = str(BASE_DIR / "preview_fast.mp4")
OUT_IMAGE = str(BASE_DIR / "first_frame.jpg")

# 2. Импорт модели
try:
    bpy.ops.wm.obj_import(filepath=str(OBJ_PATH))
except AttributeError:
    bpy.ops.import_scene.obj(filepath=str(OBJ_PATH))

coin = bpy.context.selected_objects[0]
coin.name = "DragonCoin"
bpy.context.view_layer.objects.active = coin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
coin.location = (0, 0, 0)

# Масштабирование
dim = max(coin.dimensions.x, coin.dimensions.y, coin.dimensions.z)
if dim > 0:
    coin.scale = (2.2 / dim, 2.2 / dim, 2.2 / dim)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# ==========================================================
# ТОЧНАЯ ОРИЕНТАЦИЯ МОНЕТЫ
# В исходном dragon3d.obj нормаль диска смотрит по оси Z.
# 1. Поднимаем диск вертикально (поворот по X на 90)
# 2. Проворачиваем «циферблат» по часовой стрелке (поворот по Z на -90)
# ==========================================================
coin.rotation_mode = 'XYZ'
coin.rotation_euler = (math.radians(90), 0, math.radians(-90))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Сглаживание
bpy.ops.object.shade_smooth()

# 3. Анимация вращения (2 секунды, 30 кадров для ультрабыстрого теста)
scene = bpy.context.scene
TOTAL_FRAMES = 30  # Всего 30 кадров — рендерится за 1-2 секунды!
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.fps = 15

coin.rotation_euler = (0, 0, 0)
coin.keyframe_insert(data_path="rotation_euler", frame=1)
coin.rotation_euler = (0, 0, math.radians(-360))
coin.keyframe_insert(data_path="rotation_euler", frame=TOTAL_FRAMES + 1)

if coin.animation_data and coin.animation_data.action:
    for fc in coin.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

# 4. Камера
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (0, -4.2, 0)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

# 5. Сверхбыстрый движок WORKBENCH (рендерит за 1 секунду)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'MATCAP'
scene.display.shading.color_type = 'SINGLE'
scene.render.resolution_x = 540
scene.render.resolution_y = 960

# Сохраняем первый кадр отдельно в JPG (открывается мгновенно)
scene.render.filepath = OUT_IMAGE
scene.render.image_settings.file_format = 'JPEG'
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
print(f"[+] Первый кадр сохранен: {OUT_IMAGE}")

# Сохраняем быстрое тестовое видео
scene.render.filepath = OUT_VIDEO
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.ffmpeg_preset = 'REALTIME'
scene.render.image_settings.color_mode = 'RGB'

print("[*] Рендер чернового видео (1-2 секунды)...")
bpy.ops.render.render(animation=True)
print(f"[+] Готово! Превью: {OUT_VIDEO}")