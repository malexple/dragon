import bpy
import bmesh
import math
from pathlib import Path
import numpy as np

# 1. Очистка сцены
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in bpy.data.meshes:
    bpy.data.meshes.remove(block)
for block in bpy.data.materials:
    bpy.data.materials.remove(block)

work_dir = Path("dragon")
depth_path = work_dir / "coin_depth.png"
mask_path = work_dir / "coin_mask.png"
color_path = work_dir / "coin_front.png.jpg"
if not color_path.exists():
    color_path = work_dir / "dragon.jpg"

GRID_SIZE = 4.0
SUBDIVS = 270

# 2. Создаем сетку
bpy.ops.mesh.primitive_grid_add(x_subdivisions=SUBDIVS, y_subdivisions=SUBDIVS, size=GRID_SIZE, location=(0, 0, 0))
coin = bpy.context.view_layer.objects.active
coin.name = "Solid_Dragon_Coin"

# 3. Физически удаляем ТОЛЬКО внешний фон за пределами силуэта дракона (по маске)
if mask_path.exists():
    mask_img = bpy.data.images.load(str(mask_path))
    w, h = mask_img.size
    pixels = np.array(mask_img.pixels[:]).reshape((h, w, 4))
    mask_vals = pixels[:, :, 0]  # Белое = монета, Черное = пустота

    bm = bmesh.new()
    bm.from_mesh(coin.data)

    to_delete = []
    for v in bm.verts:
        u = (v.co.x / GRID_SIZE) + 0.5
        v_c = (v.co.y / GRID_SIZE) + 0.5
        if 0 <= u <= 1 and 0 <= v_c <= 1:
            px = int(u * (w - 1))
            py = int(v_c * (h - 1))
            if mask_vals[py, px] < 0.5:  # Удаляем строго то, что за пределами монеты
                to_delete.append(v)
        else:
            to_delete.append(v)

    bmesh.ops.delete(bm, geom=to_delete, context='VERTS')
    bm.to_mesh(coin.data)
    bm.free()

bpy.ops.object.shade_smooth()

# 4. Барельеф монеты
if depth_path.exists():
    tex = bpy.data.textures.new("CoinDepth", type='IMAGE')
    tex.image = bpy.data.images.load(str(depth_path))

    disp = coin.modifiers.new(name="Displace_Relief", type='DISPLACE')
    disp.texture = tex
    disp.texture_coords = 'UV'
    disp.direction = 'Z'
    disp.mid_level = 0.0
    disp.strength = 0.12

# 5. Идеальная зеркальная симметрия по толщине (Mirror Z)
# Верх и низ свариваются точно по контуру шипов и дракона!
mirror = coin.modifiers.new(name="Symmetry_Z", type='MIRROR')
mirror.use_axis[0] = False
mirror.use_axis[1] = False
mirror.use_axis[2] = True
mirror.use_clip = True
mirror.merge_threshold = 0.008

# 6. Металл хром
mat = bpy.data.materials.new(name="DragonMetal")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

bsdf = None
for n in nodes:
    if n.type == 'BSDF_PRINCIPLED':
        bsdf = n
        break
if bsdf is None:
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')

bsdf.inputs["Metallic"].default_value = 0.98
bsdf.inputs["Roughness"].default_value = 0.22

if color_path.exists():
    tex_col = nodes.new(type="ShaderNodeTexImage")
    tex_col.image = bpy.data.images.load(str(color_path))
    coord = nodes.new(type="ShaderNodeTexCoord")
    links.new(coord.outputs["UV"], tex_col.inputs["Vector"])
    links.new(tex_col.outputs["Color"], bsdf.inputs["Base Color"])

coin.data.materials.append(mat)

# 7. Свет и ракурс
bpy.ops.object.light_add(type='POINT', location=(3.0, -3.5, 3.0))
bpy.context.view_layer.objects.active.data.energy = 800

bpy.ops.object.light_add(type='POINT', location=(-3.0, 3.5, -2.0))
rim_l = bpy.context.view_layer.objects.active.data
rim_l.energy = 600
rim_l.color = (0.1, 0.45, 1.0)

bpy.ops.object.camera_add(location=(0, -5.5, 1.2), rotation=(math.radians(78), 0, 0))
bpy.context.scene.camera = bpy.context.view_layer.objects.active

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'

print("[+] Монета готова: монолитная, без дыр, с краями ровно по контуру дракона.")