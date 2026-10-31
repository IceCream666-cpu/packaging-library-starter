# 海报到展示级 3D

## 先分清可以确认和只能估计的内容

看原海报，记录：产品个数、正面轮廓、总高宽比、盖高/瓶高比、瓶肩、可见喷嘴、透明程度、文字与标贴边界。透视侧面不直接当正面宽度。不同颜色但相同瓶型不必重复重建几何；不同结构则分别建模。

背面、底部内构、泵芯、真实壁厚和毫米尺寸在单张正面图中通常不充分。可做外观推定，并在 `model-info.json` 记录；不填假的实测值。只有工程图或实物尺寸才支持尺寸级建模。

## 选择路径

| 输入形体 | 起始配方 | 仍需校准 |
|---|---|---|
| 圆形面霜罐/广口罐 | `assets/recipes/jar.json` | 罐口、盖高、透明壁厚、内盖是否有依据 |
| 圆柱泵瓶/乳液瓶 | `assets/recipes/pump.json` | 瓶肩、泵头长短方向、罩盖、标贴 |
| 滴管精华/护理油 | `assets/recipes/dropper.json` | 胶头形状、瓶颈、滴管是否可见 |
| 方瓶/方罐 | 使用 lathe 的 `exponent`、`depth` 或圆角 box 组合 | 不能只缩放圆瓶；核对圆角与正侧面比例 |
| 软袋、异形雕塑瓶、复杂透明嵌套件 | 专用 Blender 几何 | 起始配方不足时明确改用专用模型，不强套 |

三个配方都是空白起始形体，**不是从任意海报自动识别出的成品**。由使用 Skill 的 AI 填写并调整参数，新手不用编辑。

## 配方与导出

复制配方到项目的 `model-source/<id>/spec.json`，将 `id` 改成海报 ID，`reference` 改为该海报路径。每个 part 包含 `key`、GLB `node`、中英文 `title/short/detail`、`offset` 和 `shapes`。

- `lathe` 的 `profile` 是 Blender Z 轴上的 `[高度, 半径]` 截面。可回走形成中空内壁；`depth` 控制前后比例，`exponent=2` 为圆截面，较大值接近圆角方截面。
- `box` 是 `size` 三维尺寸、`location` 中心位置和 `bevel` 圆角。
- `label` 是朝向 Blender -Y 的平面：`size=[宽,高]`，`location=[x,y,z]`，`texture` 指向配方目录内部的 PNG。PNG 内嵌进 GLB，不能引用外部绝对路径。
- `color/roughness/metallic/transmission` 控制外观。根据原海报设定；“透明”不自动等于真实玻璃。
- `offset` 是导出后 Three.js 坐标的展开距离（Y 向上、Z 向前），以归一化模型单位给出。模型总高归一到 2.9，并非 2.9 米或厘米。
- `appearance` 采用 `glass/frosted/clearLabel` 等字段。没有 `label` 部件不要启用 `clearLabel`。
- 基础查看器沿用原库的历史单款校准分支；新产品通过 `review.appearance/explosion` 配置，避免复用历史 ID 触发不相关分支。

```sh
blender --background --python-exit-code 1 \
  --python <SKILL>/scripts/build_model.py \
  -- <项目>/model-source/<id>/spec.json <项目>/model-source/<id>/v1
python <SKILL>/scripts/attach_model.py <项目> <项目>/model-source/<id>/v1
```

`--python-exit-code 1` 使脚本失败返回非零；不能只看“Blender quit”。新输出目录拒绝覆盖；修改用 v2，再在可回退的项目副本中替换模型及配置。必须把 spec、纹理、blend、GLB 与配置一起交付。

## 标签与材质不可省略

原海报包装上有品牌文字时，最终模型应保留相应文字。可从原图裁取清晰标签贴图，或根据用户给的矢量源文件制作；低清看不出的字列为待确认。普通图像处理仅用于资产准备，改变产品视觉时应使用可用的图像编辑工具并遵守用户选择。

平面标签只适合平面正面；圆瓶使用贴合曲面的 UV/曲面标签。当前基础脚本没有自动曲面贴标、雕花、螺纹或软袋褶皱生成。需要这些时复用现有查看器，扩充该款专用 Blender 源文件，不能宣称参数模板已经实现。

如原图有纸标与印刷，可分别命名 `PaperLabel`、`LogoPrint`，展开时印刷前移多于纸标；没有纸标不要虚构纸片。无盖内侧/底部参考时用注明的结构示意，不能写成真实拆解结构。

## 看图验收

并排看原海报和 3D 正面闭合图，先检查身份和轮廓，再检查盖泵、颜色材质、标签文字。随后看侧面、底部、半展、全展、回零。回零不应残留间隙或文字漂移。透明材质要在中性棚光下可见壁厚和轮廓；不能靠把透明瓶调黑来掩盖几何问题。

几何校验通过只证明文件能接入。全部视觉检查完成后才能把 `draft` 改成 `visual_reviewed`。
