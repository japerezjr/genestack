from setuptools import setup, find_packages

setup(
    name="openstack-upgrade-tools",
    version="0.1.0",
    description="Tools for upgrading OpenStack from Caracal to Epoxy",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "kubernetes>=28.0.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "hypothesis>=6.92.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openstack-upgrade=cli:main",
        ],
    },
)
