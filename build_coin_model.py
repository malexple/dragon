import bpy
import bmesh
import math
from pathlib import Path

# 1. Очистка сцены
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in bpy.data.meshes:
    bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    bpy.data.materials.remove(block)

work_dir = Path("D:/project/python/dragon")
depth_img_path = work_dir / "coin_depth.png"
color_img_path = work_dir / "coin_front.png.jpg"
if not color_img_path.exists():
    color_img_path = work_dir / "dragon.jpg"

# 2. Создаем равномерную сетку
COIN_RADIUS = 1.85
bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=260, size=4.0, location=(0, 0, 0.04))
coin = bpy.context.view_layer.objects.active
coin.name = "DragonCoin"

# 3. Обрезаем квадратную сетку ровно по кругу монеты
bm = bmesh.new()
bm.from_mesh(coin.data)
verts_to_delete = [v for v in bm.verts if (v.co.x**2 + v.co.y**2) > (COIN_RADIUS**2)]
bmesh.ops.delete(bm, geom=verts_to_delete, context='VERTS')
bm.to_mesh(coin.data)
bm.free()

bpy.ops.object.shade_smooth()

# 4. Барельеф дракона (выдавливание строго вверх по Z)
if depth_img_path.exists():
    tex_depth = bpy.data.textures.new("DepthTex", type='IMAGE')
    tex_depth.image = bpy.data.images.load(str(depth_img_path))

    disp = coin.modifiers.new(name="DragonRelief", type='DISPLACE')
    disp.texture = tex_depth
    disp.texture_coords = 'UV'
    disp.direction = 'Z'
    disp.mid_level = 0.0
    disp.strength = 0.12  # Высота дракона

# 5. Идеальная симметрия с двух сторон (Z-Mirror)
mirror = coin.modifiers.new(name="Symmetry_Z", type='MIRROR')
mirror.use_axis[0] = False
mirror.use_axis[1] = False
mirror.use_axis[2] = True  # Реверс точно повторяет аверс

# 6. Гладкий цилиндрический торец монеты
bpy.ops.mesh.primitive_cylinder_add(radius=COIN_RADIUS, depth=0.08, vertices=128, location=(0, 0, 0))
rim = bpy.context.view_layer.objects.active
rim.name = "Coin_Edge_Rim"
bpy.ops.object.shade_smooth()

bevel = rim.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.02
bevel.segments = 2

# 7. Материал полированного серебра
mat = bpy.data.materials.new(name="DragonSilverMetal")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Metallic"].default_value = 0.98
bsdf.inputs["Roughness"].default_value = 0.22

if color_img_path.exists():
    tex_img = nodes.new(type="ShaderNodeTexImage")
    tex_img.image = bpy.data.images.load(str(color_img_path))
    links.new(tex_img.outputs["Color"], bsdf.inputs["Base Color"])

coin.data.materials.append(mat)
rim.data.materials.append(mat)

# 8. Свет и камера
bpy.ops.object.light_add(type='POINT', location=(3.0, -3.0, 3.5))
bpy.context.view_layer.objects.active.data.energy = 800

bpy.ops.object.light_add(type='POINT', location=(-3.0, 3.0, 1.5))
l_rim = bpy.context.view_layer.objects.active.data
l_rim.energy = 600
l_rim.color = (0.1, 0.5, 1.0)  # Синий неоновый контур

bpy.ops.object.camera_add(location=(0, -5.5, 2.0), rotation=(math.radians(70), 0, 0))
bpy.context.scene.camera = bpy.context.view_layer.objects.active

# Включаем Material Preview во вьюпорте
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'

print("[+] Готово! Монета круглая, барельеф четкий и строго симметричный с двух сторон.")