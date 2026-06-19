import importlib
import pkgutil


def import_submodules(package_name: str) -> None:
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")
