import bpy
import math
from pathlib import Path

# ==========================================
# 1. Очистка сцены
# ==========================================
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

BASE_DIR = Path("D:/project/python/dragon")
OBJ_PATH = BASE_DIR / "dragon3d.obj"
OUT_STL = str(BASE_DIR / "dragon_medallion_print.stl")
OUT_OBJ = str(BASE_DIR / "dragon_medallion_print.obj")

# ==========================================
# 2. Импорт модели и выравнивание
# ==========================================
print(f"[*] Загрузка модели: {OBJ_PATH}")
try:
    bpy.ops.wm.obj_import(filepath=str(OBJ_PATH))
except AttributeError:
    bpy.ops.import_scene.obj(filepath=str(OBJ_PATH))

coin = bpy.context.selected_objects[0]
coin.name = "Medallion_Body"
bpy.context.view_layer.objects.active = coin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
coin.location = (0, 0, 0)

# Подъем в вертикальное положение: пирамида вершиной вверх
coin.rotation_mode = 'XYZ'
coin.rotation_euler = (math.radians(90), 0, math.radians(-90))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# ==========================================
# 3. Реальные миллиметры (Диаметр 45 мм, толщина 5 мм)
# ==========================================
TARGET_DIAMETER_MM = 45.0
TARGET_THICKNESS_MM = 5.0

curr_max_xz = max(coin.dimensions.x, coin.dimensions.z)
curr_thick = coin.dimensions.y

scale_xz = TARGET_DIAMETER_MM / curr_max_xz
scale_y = TARGET_THICKNESS_MM / curr_thick if curr_thick > 0 else scale_xz

coin.scale = (scale_xz, scale_y, scale_xz)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# ==========================================
# 4. Ювелирное ушко (сдвинуто чуть правее в ложбинку)
# ==========================================
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.5,     # Отверстие ~2.6 мм под шнурок
    minor_radius=0.5,     # Прочный пруток 1.4 мм
    major_segments=64,
    minor_segments=24,
    # Сдвинуто правее (X: -0.1 мм) и аккуратно посажено в тело обода (Z: 18.0 мм)
    location=(-0.3, 0, 16.0)
)
loop = bpy.context.active_object
loop.name = "Bail_Loop"

loop.rotation_mode = 'XYZ'
loop.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Монолитное объединение
bpy.context.view_layer.objects.active = coin
bool_mod = coin.modifiers.new(name="AttachBail", type='BOOLEAN')
bool_mod.operation = 'UNION'
bool_mod.object = loop
bool_mod.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="AttachBail")

bpy.data.objects.remove(loop, do_unlink=True)

# ==========================================
# 5. Укладка на стол для печати
# ==========================================
coin.rotation_euler = (math.radians(-90), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Пересчет нормалей наружу
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth()

# Сажаем основание на Z=0
min_z = min(v.co.z for v in coin.data.vertices)
coin.location = (0, 0, -min_z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# ==========================================
# 6. Экспорт в STL и OBJ
# ==========================================
bpy.ops.object.select_all(action='DESELECT')
coin.select_set(True)
bpy.context.view_layer.objects.active = coin

# STL для слайсеров
bpy.ops.export_mesh.stl(
    filepath=OUT_STL,
    use_selection=False,
    global_scale=1.0,
    ascii=False
)

# OBJ для мгновенного просмотра в Windows
try:
    bpy.ops.wm.obj_export(filepath=OUT_OBJ, export_selected_objects=True)
except AttributeError:
    bpy.ops.export_scene.obj(filepath=OUT_OBJ, use_selection=True)

dim_x, dim_y, dim_z = coin.dimensions.x, coin.dimensions.y, coin.dimensions.z
print("=" * 55)
print(f"[+] Экспорт завершен!")
print(f"[+] Кольцо притянуто и интегрировано в тело монеты!")
print(f"[+] Размеры детали: {dim_x:.1f} x {dim_y:.1f} x {dim_z:.1f} мм")
print(f"[+] STL для 3D-принтера: {OUT_STL}")
print(f"[+] OBJ для просмотра: {OUT_OBJ}")
print("=" * 55)