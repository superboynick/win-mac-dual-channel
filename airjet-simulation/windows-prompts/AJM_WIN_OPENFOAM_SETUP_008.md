# AJM_WIN_OPENFOAM_SETUP_008

Date: 2026-07-16
Role: Install OpenFOAM on Windows via Docker, run a simple test case, verify everything works.

## 总则

- 只读检查已完成的工作，不要用 `git reset` 或 force push
- 安装完成后在 PowerShell 截几张关键截图存入 `C:\Users\admin\Desktop\openfoam_setup\`
- 跑测试 case 时记录 Wall Time 和 log 文件的最后 20 行

---

## Step 1: 安装 Docker Desktop

打开 PowerShell（管理员），跑:

```powershell
winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
```

装完**重启 Windows**。重启后打开 Docker Desktop，等右下角图标变绿。

## Step 2: 拉取 OpenFOAM 镜像

打开 PowerShell（不需要管理员），跑:

```powershell
docker pull opencfd/openfoam-default
```

这个大约 2–3 GB，等几分钟。

拉完后验证:

```powershell
docker run --rm opencfd/openfoam-default foamExec --version
```

应该输出类似 `OpenFOAM-12` 或 `OpenFOAM-11`。

---

## Step 3: 跑一个快速测试 case

```powershell
mkdir C:\Users\admin\openfoam-test
docker run --rm -v C:\Users\admin\openfoam-test:/data -w /data opencfd/openfoam-default cp -r /usr/lib/openfoam/openfoam/tutorials/incompressible/icoFoam/cavity/cavity .
docker run --rm -v C:\Users\admin\openfoam-test:/data -w /data/cavity opencfd/openfoam-default ./Allrun
```

如果正常跑完，最后一行 log 应该有 `End`。

---

## Step 4: 截图和报告

截图存到 `C:\Users\admin\Desktop\openfoam_setup\`:

1. `docker_version.png` — PowerShell 里 `docker run --rm opencfd/openfoam-default foamExec --version` 的输出
2. `test_case_done.png` — cavity 跑完后的 log 最后 10 行
3. `docker_desktop.png` — Docker Desktop 正常运行状态

然后回复我:
```
OPENFOAM_READY=YES
VERSION=<版本号>
WALL_TIME=<cavity case 的 Wall Time>
```

---

## 如果出错

- Docker Desktop 没启动 → 点桌面图标启动，等图标变绿
- `docker: permission denied` → 用管理员 PowerShell
- 拉镜像太慢 → 正常，等就是了
- cavity 跑不动 → 把 log 文件的前 50 行发给我
