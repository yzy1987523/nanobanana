# 自动提交并推送到 GitHub
# 使用方法: .\git-push.ps1 [提交信息]

param(
    [string]$message = "auto: update project"
)

$projectDir = "c:\Custom\ToolProjects\ImageCreater\nanobanana"

cd $projectDir

# 检查是否有更改
$changes = git status --short
if (-not $changes) {
    Write-Host "没有更改需要提交" -ForegroundColor Yellow
    exit
}

# 显示更改
Write-Host "检测到更改:" -ForegroundColor Cyan
git status --short

# 添加所有更改
git add .

# 提交
Write-Host "提交更改..." -ForegroundColor Green
git commit -m $message

# 推送
Write-Host "推送到 GitHub..." -ForegroundColor Green
git push origin main

Write-Host "完成！" -ForegroundColor Green
