# file_city

import os, re, json
from body_and_soul import Soul
from basic_services import log_info, log_error, log_debug

class Variant:
    def __init__(self, inst, version, fileName="", hint=""):
        self.inst = inst
        self.version = version
        self.fileName = fileName
        self.hint = hint
        self.values = None
        self.loadErrorMsg = ""

    @property
    def varId(self):
        return self.inst.instId + '-' + Variant.format_version(self.version)

    @staticmethod
    def format_version(version):
        return "%d.%d" % version

    def is_new(self):
        return not self.fileName

    def make_file_name(self, label=""):
        hint = "".join(c for c in label if c.isalnum() or c in " .,-")
        return self.varId + "-" + hint + "." + self.inst.type.fileExt

    def load(self, defaultValues):
        if self.values is None:
            self.values = defaultValues.copy()
            if self.fileName:
                log_debug("FileCity.load", "Reading "+self.fileName)
                try:
                    with open(os.path.join(self.inst.type.db.basePath, self.fileName), mode='r', encoding='UTF-8') as f:
                        d = json.load(f)
                        self.values.update(d)
                        self.loadErrorMsg = ""
                except FileNotFoundError as e:
                    self.loadErrorMsg = "Error reading {}: File not found".format(self.fileName)
                    log_error("FileCity:", self.loadErrorMsg)
                except ValueError as e:
                    self.loadErrorMsg = "Error reading {}: {}".format(self.fileName, str(e))
                    log_error("FileCity:", self.loadErrorMsg)
            return True #Freshly loaded, or at least tried to
        else:
            return False #Already loaded

    def save(self, label=""):
        if self.values is not None:
            if not self.fileName:
                self.fileName = self.make_file_name(label)
            log_debug("FileCity.save", "Writing", self.fileName)
            with open(os.path.join(self.inst.type.db.basePath, self.fileName), mode='w', encoding='UTF-8') as f:
                json.dump(self.values, f, indent=2, sort_keys=True)
            self.loadErrorMsg = ""

class FileCitySoul(Soul):
    def __init__(self, variant):
        super().__init__()
        self.inst = variant.inst
        self.curVariant = variant
        self.values = self.curVariant.values

    def copy(self):
        return FileCitySoul(self.curVariant)

    def load(self, defaultValues, version='current'):
        if version != 'current':
            self.curVariant = self.inst.find_variant(version, self.curVariant)
        freshLoad = self.curVariant.load(defaultValues)
        self.values = self.curVariant.values
        return freshLoad

    # save has two steps
    # step 1, find variant that we want to save into, and update its values with newValues
    def save_update(self, newValues, version='advance'):
        if self.values is None:
            raise Exception("Soul must be loaded before saving")
        if version != 'current':
            self.curVariant = self.inst.find_variant(version, self.curVariant)
        if self.curVariant.values is not self.values:
            self.curVariant.values = self.values.copy()
            self.values = self.curVariant.values
        self.values.update(newValues)

    # step 2, write values to persistent storage
    def save_write(self, label=""):
        self.curVariant.save(label)

    def get_hint_label(self):
        return self.curVariant.hint

    def get_inst_id(self):
        return self.inst.instId

    def is_new(self):
        return self.curVariant.is_new()

    def get_load_error_msg(self):
        return self.curVariant.loadErrorMsg

    def get_version(self, version='current'):
        variant = self.inst.find_variant(version, self.curVariant)
        if variant is not None:
            return variant.version
        else:
            return None

    @staticmethod
    def format_version(version):
        return Variant.format_version(version)

    @staticmethod
    def is_same_minor_series(version1, version2):
        return version1[0] == version2[0]

class Instance:
    def __init__(self, myType, instNum):
        self.type = myType
        self.instNum = int(instNum)
        self.variants = []

    @property
    def instId(self):
        return "%s%04d" % (self.type.tag, self.instNum)

    def add_variant(self, version, fileName="", hint=""):
        newVar = Variant(self, version, fileName, hint)
        self.variants.append(newVar)
        log_debug("FileCity.add_variant", "Added variant", newVar.varId)
        return newVar

    def sort_variants(self):
        self.variants.sort(key=lambda var: var.version)
        previousVer = None
        for var in self.variants:
            if var.version == previousVer:
                raise ValueError("Duplicate version:", var.varId)
            previousVer = var.version

    def find_variant(self, version, curVariant=None):
        if version == 'current':
            return curVariant
        elif version == 'previous':
            return self.get_previous(curVariant)
        elif version == 'next':
            return self.get_next(curVariant)
        elif version == 'first':
            return self.get_first()
        elif version == 'latest':
            return self.get_latest()
        elif version == 'advance' or version == 'advance_minor':
            return self.add_next_minor_version(curVariant)
        elif version == 'advance_major':
            return self.add_next_major_version()
        else:
            for var in self.variants:
                if var.version == version:
                    return var
            return None

    def get_previous(self, curVariant):
        i = self.variants.index(curVariant)
        if i > 0:
            return self.variants[i-1]
        else:
            return None

    def get_next(self, curVariant):
        i = self.variants.index(curVariant)
        if i < len(self.variants)-1:
            return self.variants[i+1]
        else:
            return None

    def get_first(self):
        if self.variants:
            return self.variants[0]
        else:
            return self.add_next_minor_version()

    def get_latest(self):
        if self.variants:
            return self.variants[-1]
        else:
            return self.add_next_minor_version()

    def get_next_minor_version(self, curVariant=None):
        if curVariant is not None:
            curMajor = curVariant.version[0]
            lastMinor = curVariant.version[1]
            for var in self.variants[self.variants.index(curVariant)+1:]:
                if var.version[0] != curMajor:
                    break
                else:
                    lastMinor = var.version[1]
            return curMajor, lastMinor+1
        elif self.variants:
            latest = self.variants[-1]
            return latest.version[0], latest.version[1]+1
        else:
            return 1,0

    def get_next_major_version(self):
        if self.variants:
            latest = self.variants[-1]
            return latest.version[0]+1, 0
        else:
            return 1,0

    def add_next_minor_version(self, curVariant=None):
        if curVariant is None or not self.variants or self.variants[-1] is curVariant:
            # just append to end of list, no sort necessary
            return self.add_variant(self.get_next_minor_version())
        else:
            # general case where new version may not go at end of list
            newVar = self.add_variant(self.get_next_minor_version(curVariant))
            self.sort_variants()
            return newVar

    def add_next_major_version(self):
        return self.add_variant(self.get_next_major_version())

    def make_body(self, variant=None):
        if variant is None:
            variant = self.get_latest()
        return self.type.bodyClass(FileCitySoul(variant))

class Type:
    def __init__(self, db, tag, bodyClass, fileExt):
        self.db = db
        self.tag = tag
        self.fileExt = fileExt
        self.instances = {}
        self.nextInstNum = 1
        self.bodyClass = bodyClass

    def add_instance(self, instNum):
        instNum = int(instNum)
        if instNum in self.instances:
            raise ValueError("Duplicate instance: "+self.instances[instNum].instId)
        newInst = Instance(self, instNum)
        self.instances[instNum] = newInst
        log_debug("FileCity.add_instance", "Added instance", newInst.instId)
        if instNum >= self.nextInstNum:
            self.nextInstNum = instNum + 1
        return newInst

    def generate_all(self):
        return (inst.make_body() for instNum, inst in self.instances.items())

    def make_new(self, hint=""):
        newInst = self.add_instance(self.nextInstNum)
        newInst.add_variant(newInst.get_next_minor_version(), hint=hint)
        return newInst.make_body()

class FileCity:
    def __init__(self):
        self.types = {}
        self.fileNameRe = re.compile(r"([A-Z]+)(\d+)-(\d+)\.(\d+)-(.*)\.([A-Z]+)", re.IGNORECASE)
        self.variantRe = re.compile(r"([A-Z]+)(\d+)-(\d+)\.(\d+)", re.IGNORECASE)
        self.instRe = re.compile(r"([A-Z]+)(\d+)", re.IGNORECASE)

    def add_type(self, tag, variantClass, fileExt="json"):
        newType = Type(self, tag, variantClass, fileExt.lower())
        self.types[tag] = newType
        log_debug("FileCity", "Added type", tag)
        return newType

    def get_type(self, tag):
        if tag in self.types:
            return self.types[tag]
        else:
            raise ValueError("No such type: "+tag)

    def open(self, basePath):
        log_info("FileCity: Opening", basePath)
        self.basePath = basePath
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        self.scan_directory()
        self.sort_variants()

    def scan_directory(self):
        for fileName in os.listdir(self.basePath):
            filePath = os.path.join(self.basePath, fileName)
            if os.path.isfile(filePath):
                try:
                    self.scan_file(fileName)
                except ValueError as e:
                    log_error("FileCity.scan_directory:", e.args)

    def scan_file(self, fileName):
        match = self.fileNameRe.match(fileName)
        if match:
            tag = match.group(1)
            if tag in self.types:
                theType = self.types[tag]
                fileExt = match.group(6).lower()
                if fileExt == theType.fileExt:
                    instNum = int(match.group(2))
                    version = (int(match.group(3)), int(match.group(4)))
                    hint = match.group(5)
                    if instNum not in theType.instances:
                        theType.add_instance(instNum)
                    inst = theType.instances[instNum]
                    inst.add_variant(version, fileName, hint)

    def sort_variants(self):
        for tag, theType in self.types.items():
            for instNum, inst in theType.instances.items():
                try:
                    inst.sort_variants()
                except ValueError as e:
                    log_error("FileCity.sort_variants:", e.args)

    def lookup(self, instOrVarId):
        match = self.variantRe.match(instOrVarId)
        if match:
            tag = match.group(1)
            if tag in self.types:
                theType = self.types[tag]
                instNum = int(match.group(2))
                version = (int(match.group(3)), int(match.group(4)))
                if instNum in theType.instances:
                    inst = theType.instances[instNum]
                    var = inst.find_variant(version)
                    return inst.make_body(var)
        else:
            match = self.instRe.match(instOrVarId)
            if match:
                tag = match.group(1)
                if tag in self.types:
                    theType = self.types[tag]
                    instNum = int(match.group(2))
                    if instNum in theType.instances:
                        inst = theType.instances[instNum]
                        var = inst.get_latest()
                        return inst.make_body(var)
        return None

    def generate_all(self, tag):
        return self.get_type(tag).generate_all()

    def make_new(self, tag, hint=""):
        return self.get_type(tag).make_new(hint)
