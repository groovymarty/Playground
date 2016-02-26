# basic_logger

import os, time

class BasicLogger:
    def __init__(self, basePath, logFileName, echoStdout=False):
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        self.logFilePath = os.path.join(basePath, logFileName)
        self.logFile = None
        self.anyError = False
        self.debugTags = {"All": False}
        self.echoStdout = echoStdout

    def __enter__(self):
        self.open_log()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_log()

    def __del__(self):
        self.close_log()

    def open_log(self):
        if self.logFile == None:
            self.logFile = open(self.logFilePath, mode="a", encoding="utf-8")

    def close_log(self):
        if self.logFile != None:
            self.logFile.close()
            self.logFile = None

    def log(self, *args, level="Info"):
        timestamp = time.strftime("%c")
        if self.logFile != None:
            print(timestamp, level, *args, file=self.logFile)
        if self.echoStdout:
            print(timestamp, level, *args)

    def log_info(self, *args):
        self.log(*args, level="Info")

    def log_error(self, *args):
        self.log(*args, level="Error")
        self.anyError = True

    def log_debug(self, tag, *args):
        enabled = self.debugTags["All"]
        tagPart = tag
        while tagPart:
            if tagPart in self.debugTags:
                enabled = self.debugTags[tagPart]
                break
            else:
                tagPart = tagPart.rpartition(".")[0]
        if enabled:
            self.log("["+tag+"]:", *args, level="Debug")

    def enable_debug(self, *args):
        for tag in args:
            self.debugTags[tag] = True
            self.log_info("Logger: ["+tag+"] enabled")

    def disable_debug(self, *args):
        for tag in args:
            self.debugTags[tag] = False
            self.log_info("Logger: ["+tag+"] disabled")
