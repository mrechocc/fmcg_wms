from setuptools import find_packages, setup


setup(
    name="fmcg_wms",
    version="0.4.0",
    description="FMCG warehouse management controls for ERPNext",
    author="快消品WMS系统",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
