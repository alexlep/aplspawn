import os
from helpers import exec_command, checkOutput, OK, FAIL, INFO, createDir

class Paths(object):
    def __init__(self, dConfig):
        self.c = dConfig

    def checkWorkingDirs(self):
        step = "Checking if working directories exist"
        failed = False
        for path in self.c.getValues():
            if not os.path.exists(path):
                print(FAIL(path))
                failed = True
        if not failed:
            print(OK(step))
        else:
            print(FAIL(step))

    @checkOutput
    def createWorkingDirs(self):
        res, msg = False, True
        step = "Creating working directories"
        try:
            for path in self.c.getValues():
                createDir(path)
            res = True
        except Exception as e:
            msg = e
        return res, msg, step

    @checkOutput
    def rmWorkingDirs(self):
        step = "Removing content of working directories"
        wd = self.c.workingDirectory
        for key in self.c.getKeys():
            path = getattr(self.c, key)
            if key == "workingDirectory":
                continue
            if wd in path:
                if os.path.isdir(path):
                    msg, ec = exec_command ("sudo rm -rf {0}/*".format(path))
                    print(OK(path + " was cleaned up"))
            else:
                print(INFO("{} is not under parent working directory," \
                           " refusing to remove it's cintent").format(path))
        return True, "", step

    def checkStatus(self):
        self.checkWorkingDirs()
