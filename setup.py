from setuptools import find_packages, setup

setup(
    name="faceforge",
    version="2.0.0",
    description="FaceForge — AI face swap & restoration studio",
    packages=find_packages(exclude=("tests",)),
    py_modules=["run"],
    python_requires=">=3.10",
    entry_points={"gui_scripts": ["faceforge=run:main"]},
)
