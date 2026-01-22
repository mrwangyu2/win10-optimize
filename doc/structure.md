# 项目文件结构

```text
win10_optimize/
├── README.md               # 项目总览和快速入门
├── main.py                 # 程序入口
├── build_exe.bat           # 打包脚本
├── run.bat                 # 运行脚本
├── requirements.txt        # 依赖列表
├── config/                 # 配置文件目录
│   └── win10_optimize_profile.json  # 核心优化任务定义
├── core/                   # 核心逻辑
│   ├── profile_parser.py   # 配置解析
│   ├── executor.py         # 任务调度
│   ├── system_checker.py   # 环境检查
│   └── ...
├── executors/              # 具体执行器
│   ├── service_executor.py # 服务操作
│   ├── registry_executor.py# 注册表操作
│   └── ...
├── ui/                     # 界面组件
│   ├── main_window.py      # 主窗口
│   ├── task_selector.py    # 任务选择
│   ├── bandwidth_selector.py # 网络配置
│   └── update_pause_selector.py # 更新策略
└── doc/                    # 文档和资源
    ├── demo_2.gif          # 功能展示图
    ├── implementation.md   # 技术实现文档
    └── deployment.md       # 部署说明文档
```
