from setuptools import setup, find_packages

setup(
    name="faceforge",
    version="1.0.0",
    description="FaceForge — Open-source AI Face Swap & Enhancement Tool",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        # Dependencies are managed in requirements.txt
    ],
    entry_points={
        "console_scripts": [
            "faceforge=run:main",
        ],
    },
)
