class BuildStatusDetails:
    def __init__(self, line):
        line = line.replace ('\r', "")
        line = line.replace ('\n', "")
        data = line.split(" ")
        self.server = data [0]
        self.platform = data [1]
        self.componentGroup = data [2]
        self.component = data [3]
        self.branch = data [4]
        self.shortbranch = data [5]
        self.configId = data [6]
        self.configPath = data [7]
        self.buildType = data [8]
        self.configGuid = data [9]
        self.buildVersion = data [10]
        self.buildEndDateISO = data [11]
        self.buildUrl = data [12]
        self.buildStatus = data [13]
        self.nicebranch = data [14]