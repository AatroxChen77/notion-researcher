from setuptools import setup, find_packages

setup(
    name="notion-pusher",    # 项目的内部包名
    version="0.5.0",         # 版本号，随便写
    packages=find_packages(), # 自动寻找 src 目录
    py_modules=["main"],      # 关键：告诉它 main.py 也是代码的一部分
    install_requires=[        # 依赖包，安装时会自动检查
        "notion-client",
        "PyYAML",
    ],
    entry_points={
        'console_scripts': [
            # 魔法在这里：左边是你想敲的命令，右边是"文件名:函数名"
            'np=main:main', 
        ],
    },
)