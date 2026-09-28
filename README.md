<div align="center">

<img src="icon-192-v2.png" width="96" alt="ZCode Remote PWA">

# ZCode Remote PWA

**把 ZCode 桌面端的「移动端远程控制」装进手机桌面**
一个无后端、零配置、开箱即用的开源 PWA 壳

[在线安装](https://zylzyqzz.github.io/zcode-remote-pwa/) · [使用说明](#-使用) · [常见问题](#-faq) · [自行部署](#-自行部署)

`ZCode` `PWA` `移动端` `远程控制` `开源`

</div>

---

> **English**: A backend-free PWA wrapper that turns ZCode desktop's "Mobile Remote Control" QR link into an installable home-screen app. Scan **your own** QR code, control **your own** workspace. No accounts, no server, no tracking — the link never leaves your phone.

## 📖 这是什么

[ZCode](https://z.ai) 桌面客户端自带「移动端远程控制」：扫二维码即可在手机上查看和控制工作区会话。
但那个链接每次都以普通网页打开——没有图标、没有全屏、体验割裂。

本项目把它包成一个标准 PWA：

| | |
|---|---|
| 📱 **安装到桌面** | 独立窗口运行，官方 Z 图标，像原生 App |
| 🪟 **迷你悬浮窗** | 任务页一键缩到右上角实时缩略，点按弹出完整窗口 |
| 📷 **一键传图** | 手机拍照/选相册 → 自动上传图床 → 链接复制，粘贴到对话即可让 agent 取图 |
| 🔍 **扫码配置** | App 内直接扫电脑上的二维码，不用手动搬链接 |
| 🔍 **等比缩放** | 50%–100% 五档缩放，小屏看更多内容，偏好自动记忆 |
| 🔗 **换码友好** | 电脑端刷新二维码后，长按小窗重新扫码即可，无需重装 |

**无后端 · 无统计 · 无登录**：壳是纯静态文件，你的远程链接只存在你自己手机的 localStorage 里，仓库不含任何人的链接。

| 配置页 | 迷你悬浮窗 |
|---|---|
| <img src="docs/screenshot-setup.png" width="270" alt="配置页"> | <img src="docs/screenshot-mini.png" width="270" alt="迷你悬浮窗"> |

## 🚀 快速开始

1. 手机浏览器打开 **https://zylzyqzz.github.io/zcode-remote-pwa/**
2. 浏览器菜单 → **「添加到主屏幕 / 安装应用」**
3. 电脑端 ZCode → 左下角「**移动端远程控制**」→ 点「复制链接」或亮出二维码
4. 打开 App → 「**📷 扫码配置**」对准电脑上的二维码（或粘贴链接）
5. 完成，开始遥控 🎉

## 📱 使用

| 操作 | 说明 |
|---|---|
| 展开态右上角 **–** | 任务页缩成右上角迷你窗（实时画面，非截图） |
| **点迷你窗** | 弹出完整任务窗口 |
| **长按迷你窗** | 打开设置：重新扫码 / 传图 / 缩放 |
| 展开态右上角 **📷** | 拍照或选图上传图床，链接自动复制 → 粘贴到对话发送 |
| 设置里 **缩放** | 会话页 50%–100% 等比缩放，自动记忆 |

> 💡 传图的原理是把图片传到公共图床（tmpfiles.org → sm.ms → catbox.moe 依次尝试），然后把下载链接复制给你。粘贴到对话里发一句"把这张图下载到工作区"，agent 就能看到图片了。

## ❓ FAQ

<details>
<summary><b>安装一直转圈 / 卡在一半？</b></summary>

Chrome 安装 WebAPK 需要连接 Google 的生成服务器，国内网络经常卡住。两个办法：

1. 开着代理点一次「安装」，装好后日常使用**不需要**代理；
2. 直接用浏览器菜单的「**添加到主屏幕**」，不经过 WebAPK，同样有独立窗口体验。
</details>

<details>
<summary><b>图标 / 界面还是旧版？</b></summary>

GitHub Pages 有 10 分钟缓存，浏览器还有自己的缓存。把 App 彻底关掉重开一次（Service Worker 会自动拉新）；桌面图标要更新就删掉重新「添加到主屏幕」。
</details>

<details>
<summary><b>二维码会失效吗？</b></summary>

会。电脑端点「刷新二维码」后旧链接立即作废——App 里**长按迷你窗 → 重新扫码**即可，不用重装。
</details>

<details>
<summary><b>别人扫我的码会冲突吗？</b></summary>

连接按设备独立，互不挤掉，多人可同时查看同一会话；但<strong>同时发指令</strong>会交错执行，约定一次一人发即可。
<br><br>⚠️ <b>二维码 = 工作区钥匙</b>：扫了就能看全部对话并控制工作区，别给不信任的人扫；泄露后到桌面端「刷新二维码」立即作废。
</details>

<details>
<summary><b>会收集我的数据吗？</b></summary>

不会。壳是纯静态文件，链接只存在你手机本地。唯一外发数据是你<b>主动选择上传</b>的图片（上传到公共图床，链接 1 小时～永久有效视图床而定）。
</details>

<details>
<summary><b>iOS 能用吗？</b></summary>

iPhone Safari 支持「添加到主屏幕」，核心功能一致（未深度测试，欢迎提 issue）。
</details>

## ⚙️ 工作原理

```
┌─────────────────────────────┐
│  PWA 壳（本仓库，纯静态）      │
│                             │
│  ┌───────────────────────┐  │
│  │ iframe                │  │
│  │ zcode.z.ai/remote/v4  │  │  ← 扫码得到的链接（存于手机 localStorage）
│  │ （ZCode 官方远程页）     │  │
│  └───────────────────────┘  │
│  迷你窗 = 同一 iframe 等比缩略 │
│  传图 = FormData → 公共图床   │
└─────────────────────────────┘
```

- 壳只负责：装载 iframe、迷你窗缩略、扫码（BarcodeDetector + jsQR 兜底）、图床上传、缩放记忆
- 不含构建工具、框架依赖与任何后端
- ZCode 远程页本身的 UI（对话、待办行等）由 ZCode 官方渲染，壳无法也不试图修改

## 🛠 自行部署

不需要构建，把静态文件扔到任意 HTTPS 托管即可：

```bash
git clone https://github.com/zylzyqzz/zcode-remote-pwa.git
cd zcode-remote-pwa

# 本地预览（任选其一）
python -m http.server 8080          # http://localhost:8080
npx serve .                         # 或
```

部署到 GitHub Pages / Vercel / Cloudflare Pages 均为纯静态发布。
建议部署**自己的副本**并替换图标与名称，避免和本项目混淆。

> ⚠️ 无论怎么部署，都不要把自己的远程链接（含 hash）写进任何公开文件。

## 📁 目录结构

```
zcode-remote-pwa/
├── index.html              # 壳主体：配置页 / 任务窗 / 迷你窗 / 设置 / 传图
├── manifest.webmanifest    # PWA 清单（名称、图标、独立窗口）
├── sw.js                   # Service Worker（壳离线缓存，跨域页面不缓存）
├── icon-192-v2.png         # 官方 Z 图标 192
├── icon-512-v2.png         # 官方 Z 图标 512
├── icon-maskable-512-v2.png# 自适应图标（Android）
├── jsqr.js                 # jsQR 1.4.0（老设备扫码兜底）
├── docs/                   # 截图
├── official-icon.png       # ZCode 官方图标原图 1024×1024（生成图标的源素材）
├── make-icons-v2.ps1       # 图标生成脚本（PowerShell + GDI+ 缩放/自适应）
├── serve.ps1               # 本地静态服务器（Windows 测试用，可选）
└── push-via-api.ps1        # GitHub Contents API 部署脚本（token 走环境变量 GH_TOKEN）
```

## 🤝 贡献

欢迎 issue / PR：新图床支持、iOS 适配、UI 打磨都欢迎。

## 📄 License

[MIT](LICENSE) © 2026 zylzyqzz

> 本项目为独立的第三方工具，与 ZCode / 智谱官方无关；ZCode 及其图标版权归原权利方所有。
