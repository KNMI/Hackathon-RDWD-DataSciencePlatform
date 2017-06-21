from pywps.Process import WPSProcess
import wrangler.wrangleCSV_NCDF as wrangler
import sys, logging, types, os, time, tempfile

class WrangleProcess(WPSProcess):
    def __init__(self):
        # init process
        WPSProcess.__init__(self,
                            identifier = "wrangleProcess", # must be same, as filename
                            title="Wrangle process",
                            version = "0.1",
                            storeSupported = "true",
                            statusSupported = "true",
                            abstract=("The wrangle process accepts the relative path of a "
                                      "CSV file in the basket, as well as a relative path "
                                      "to the metadata description of the CSV file and a "
                                      "description of the process. "
                                      "The result of the process is a wrangled CSV file."),
                            grassLocation =False)

        self.inputCSVPath = self.addLiteralInput(identifier = "inputCSVPath",
                                                 title = ("The path/URL to the input CSV file "
                                                          "which needs to be wrangled"),
                                                 type="String")

        self.metaCSVPath = self.addLiteralInput(identifier="metaCSVPath",
                                                title=("The path to the metadata describing "
                                                       "the CSV file in JSON format"),
                                                type="String")

        self.jobDescPath = self.addLiteralInput(identifier="jobDescPath",
                                                title=("A path to the description of the "
                                                       "parameters which should be added "
                                                       "to the input CSV"),
                                                type="String")

        self.limit = self.addLiteralInput(identifier="limit",
                                          title=("An optional limit in the amount of lines "
                                                 "which should be processed"),
                                          type=types.IntType,
                                          default=-1)

        self.outputURL = self.addLiteralOutput(identifier="outputURL",
                                               title="The url to the output CSV file",
                                               type="String")
        self.percentComplete = 0

    def statusCallback(self, message, percentComplete=0):
        # self.percentComplete += percentComplete
        self.percentComplete = percentComplete
        if self.percentComplete >= 100: self.percentComplete = 100
        self.status.set(message, self.percentComplete)
        
    def execute(self):

        inputCSVPath = self.inputCSVPath.getValue()
        inputCSVPath_t = os.path.splitext(inputCSVPath)
        outputFileName = inputCSVPath_t[0]+"_wrangled"+inputCSVPath_t[1]
        metaCSVPath = self.metaCSVPath.getValue()
        jobDescPath = self.jobDescPath.getValue()
        limit = self.limit.getValue()

        currentBasket = inputCSVPath_t[0]+"_"+time.strftime("%Y%m%dt%H%M%S"+"_")
        pathToBasket = os.environ['POF_OUTPUT_PATH']

        basket = tempfile.mkdtemp(prefix=currentBasket, dir=pathToBasket)
        urlToBasket  = os.environ['POF_OUTPUT_URL']+"/"+basket[len(pathToBasket):]

        dwp_dict = {"inputCSV":basket+"/../../"+inputCSVPath,
                    "metaCSV":basket+"/../../"+metaCSVPath,
                    "jobDesc":basket+"/../../"+jobDescPath,
                    "logFile":basket+"/"+inputCSVPath_t[0]+".log",
                    "statusCallback":self.statusCallback,
                    "limitTo":limit}
        try:
            dwp = wrangler.dataWranglerProcessor()
            dwp.Initialize(dwp_dict)
            dwp.ReadInputCSV()
            self.status.set("Starting the wrangling process.", 0)
            dwp.WrangleWithNetCdfData({"outputCSV":basket+"/"+outputFileName})
        except Exception, e:
            self.status.set(e, 500)
            raise e
            return 1

        self.outputURL.setValue(urlToBasket+"/"+outputFileName)
        self.status.set("Ready", 100)
