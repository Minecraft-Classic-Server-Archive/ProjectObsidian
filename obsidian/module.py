from dataclasses import dataclass
from typing import Type
import importlib

from obsidian.constants import InitError, MODULESIMPORT, MODULESFOLDER
from obsidian.utils import getFiles
from obsidian.log import Logger

# Module Skeleton
@dataclass
class AbstractModule():
    # Defined Later In _ModuleManager
    NAME: str = ""
    DESCRIPTION: str = ""
    VERSION: str = ""


# Internal Module Manager Singleton
class _ModuleManager():
    def __init__(self):
        # Creates List Of Modules That Has The Module Name As Keys
        self._module_list = {}
        self._completed = False

    # Registration. Called by Module Decorator
    def register(self, name: str, description: str, version: str, module: Type[AbstractModule]):
        Logger.debug(f"Registering Module {name}", module="init-" + name)
        from obsidian.packet import PacketManager  # Prevent Circular Looping :/
        obj = module()  # Create Object
        # Attach Values As Attribute
        obj.NAME = name
        obj.DESCRIPTION = description
        obj.VERSION = version
        for _, item in module.__dict__.items():  # Loop Through All Items In Class
            if hasattr(item, "obsidian_packet"):  # Check If Item Has "obsidian_packet" Flag
                packet = item.obsidian_packet
                # Register Packet Using information Provided By "obsidian_packet"
                PacketManager.register(
                    packet["direction"],
                    packet["name"],
                    packet["description"],
                    packet["packet"],
                    obj
                )
        self._module_list[name] = obj

    # Function to libimport and register all modules
    # EnsureCore ensures core module is present
    def initModules(self, blacklist=[], ensureCore=True):
        if not self._completed:
            Logger.info("Initializing Modules", module="init")
            blacklist.append("__init__")  # Force Ignoring Init File
            if ensureCore:
                try:
                    importlib.import_module(MODULESIMPORT + "core")
                    blacklist.append("core")  # Adding core to whitelist to prevent re-importing
                    Logger.info("Loaded (mandatory) Module core", module="init")
                except ModuleNotFoundError:
                    Logger.fatal("Core Module Not Found! (Failed ensureCore). Check if 'core.py' module is present in modules folder!")
                    raise InitError("Core Module Not Found!")
                except Exception as e:
                    raise e
            # Get list of all modules
            detectedModules = getFiles(MODULESFOLDER, extention=".py", removeExtention=True)
            # print(detectedModules)
            for module in detectedModules:
                if module not in blacklist:
                    try:
                        importlib.import_module(MODULESIMPORT + module)
                        Logger.info(f"Loaded Module {module}", module="init")
                    except ModuleNotFoundError:
                        Logger.fatal("Module Not Found!!! This should NOT happen!")
                        raise InitError(f"Module {module} Not Found!")
                    except Exception as e:
                        raise e
        else:
            Logger.info("Modules Already Initialized; Skipping.", module="init")

    # Handles _ModuleManager["item"]
    def __getitem__(self, module: str):
        return self._module_list[module]

    # Handles _ModuleManager.item
    def __getattr__(self, *args, **kwargs):
        return self.__getitem__(*args, **kwargs)


# Module Registration Decorator
def Module(name: str, description: str = None, version: str = None):
    def internal(cls):
        ModuleManager.register(name, description, version, cls)
    return internal


# Creates Global ModuleManager As Singleton
ModuleManager = _ModuleManager()
# Adds Alias To ModuleManager
Modules = ModuleManager