# 从输入到交付

## 给使用者的两个输入

1. 提供 PNG、JPG、JPEG 或 WebP 海报，可以一次多张。优先原尺寸，产品主体和包装文字尽量清楚。
2. 选择自然温润、清透简洁或鲜明活泼。未选择采用自然温润。

库名可以从品牌读取，用户未指定时先用“我的包材库”。产品有歧义时可一次集中询问关键问题；不要询问本可从原海报读到的信息。新手仍需目视确认产品有没有做错；这是产品验收，不是开发工作。

## 环境由 AI 处理

- 网页：Node.js，版本需满足附带 Vite 的 `engines`。本次验证运行时版本记录在交付报告；不要把旧机器目录写入工程。
- 图片导入：Python 3.10+ 和 Pillow。导入前先检查 `python -c "import PIL"`；缺少时在项目外建立独立虚拟环境安装，避免更改系统 Python。
- 3D：Blender 4.5 系列已用于本次模板导出验证；可用系统 `blender` 或用户已安装位置。
- 新电脑前端使用 `npm ci`，再 `npm run dev`。依赖名称和版本已保留；仓库提供 package-lock.json，仓库版将另做干净依赖安装验证；结果见根目录 docs/repository-validation.json。勿把 node_modules 打进移交 ZIP。
- 首次装软件/工具属于一次性准备；之后每批工作应尽量回到海报+风格两个输入。付费 AI 生成服务不是这套基础模板的必需依赖。

## 新建与样例

把本 Skill 整个目录保留在一起；资源路径相对 Skill 解析，工作目录可不同。

```sh
python <SKILL>/scripts/new_project.py --posters <海报目录> --out <新项目目录> --style clear --name "新品牌包材库"
cd <新项目目录>
npm ci
npm run dev
```

第一次可直接复制 `assets/starter/` 跑三款样例。示例海报与模型属于原项目素材；用于学习或经授权的内部复用，不是新使用者自己的产品和品牌资产。

`new_project.py` 先检查图片，再在临时目录准备，最后交付新目录。输入图片按字节保留，派生预览使用 WebP。同字节重复海报合并；内容变化会产生新 ID。若用户只是修订已存在海报，人工保留原 ID 并更新素材摘要，不把图片哈希 ID 误当成永不变的产品身份。

## 项目文件映射

| 位置 | AI 在这里做什么 |
|---|---|
| `intake.json` | 原文件名、摘要、阶段与不确定信息；随制作更新状态 |
| `src/brand.json` | 库名、英文名、首页标题 |
| `src/posters.json` | 产品名、原图和预览路径、类别及风格标签 |
| `src/featured.json` | 首页顺序、产品背景、文字对比、产品描述 |
| `src/featured-media.json` | 首页响应式图像；后续用真实抠图替换完整海报 |
| `src/structure/collection-products.json` | 当前已接入模型、部件节点、材质外观、展开配置 |
| `public/assets/packaging/` | 实际 GLB 及动画库 |
| `public/assets/` | 海报原图与预览图 |
| `public/featured/` | 首页展示图 |

状态建议：`poster_ready → modeling → draft → visual_reviewed → delivered`。仅正式发布有依据时增加 `published`。首页具有海报不等于模型已完成；当前底座可展示暂未制作 3D 的海报。

## 完整流水线

海报导入 → AI 看图识别 → 按产品选择形体配方 → 制作/修订 3D → 贴图与部件命名 → 本地接入 → 闭合/半展/全展检查 → 手机视口检查 → 源文件与预览打包。

框架固定网页、交互和数据连接；变动内容限于当前产品的素材、几何、文案与视觉配置。不能为了新产品把整个查看器重写一遍。
