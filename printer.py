import os
import subprocess
from packaging import version
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import glob
import locale
import ghostscript
#import string
#import codecs

# get the location of ghostscript
# if os.name == 'nt':
#     GHOSTSCRIPT_APP = None
#     for gsDir in [os.environ['ProgramFiles'] + os.sep + 'gs', os.environ['ProgramFiles(x86)'] + os.sep + 'gs']:
#         if os.path.isdir(gsDir):
#             # find the newest version
#             bestVersion = '0'
#             for f in os.listdir(gsDir):
#                 path = gsDir + os.sep + f
#                 if os.path.isdir(path) and f.startswith('gs'):
#                     try:
#                         val = f[2:]
#                     except:
#                         val = '0'
#                     if version.parse(bestVersion) < version.parse(val):
#                         for appName in ['gswin64c.exe', 'gswin32c.exe', 'gswin.exe', 'gs.exe']:
#                             appName = gsDir + os.sep + f + os.sep + 'bin' + os.sep + appName
#                             if os.path.isfile(appName):
#                                 bestVersion = val
#                                 GHOSTSCRIPT_APP = '"' + appName + '"'
#                                 break
#     if GHOSTSCRIPT_APP is None:
#         errString = """ERR: Ghostscript not found!
# 			You can get it from:
# 				http://www.ghostscript.com"""
#         raise Exception(errString)
# else:  # assume we can find it
#     GHOSTSCRIPT_APP = 'gs'
# print('GHOSTSCRIPT_APP=' + GHOSTSCRIPT_APP)

# find a good shell_escape routine
try:
    import shlex

    if hasattr(shlex, 'quote'):
        shell_escape = shlex.quote
    else:
        import pipes

        shell_escape = pipes.quote
except ImportError:
    import shlex
    import pipes

    shell_escape = pipes.quote


class Printer(object):
    """
	You can derive from this class to create your own printer!
	Simply send in the options you want in Printer.__init__
	and then override printThis() to do what you want.
	DONE!
	Ready to run it with run()
	"""

    def __init__(self, name='My Virtual Printer', acceptsFormat='pdf', acceptsColors='rgba'):
        """
		name - the name of the printer to be installed
		acceptsFormat - the format that the printThis() method accepts
		Available formats are "pdf", or "png" (default=png)
		acceptsColors - the color format that the printThis() method accepts
		(if relevent to acceptsFormat)
		Available colors are "grey", "rgb", or "rgba" (default=rgba)
		"""
        self._server = None
        self.name = name
        self.acceptsFormat = acceptsFormat
        self.acceptsColors = acceptsColors
        self.bgColor = '#ffffff'  # not sure how necessary this is


    def printThis(self, doc, title=None, author=None):
        """
		you probably want to override this
		called when something is being printed
		defaults to saving a file
		TODO: keep track of filename?
		"""
        # for i in doc1:
        #     if '/Title ' in i:
        #         element = i.split()
        #         print(element)
        #         element = element[1:-2]
        #         print(element)
        #
        #         for i in element:
        #             print(type(i))
        #             out = i.translate(str.maketrans("", "", string.punctuation))
        #             print(out)
        #
        # if title is None:
        #     title = 'printed'
        # if author != None:
        #     title = title + ' - ' + author

        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)
        #title = self.filename2(doc, title=title, author=author)
        #print(title)
        # f = open(shell_escape(title + '.' + self.acceptsFormat), 'wb+')
        # f.write(doc)
        # f.close()
        path = os.getcwd()
        print("Uploading File.....")
        for x in glob.glob("*.pdf"):
            f1 = drive.CreateFile({'title': x})
            f1.SetContentFile(os.path.join(path, x))
            f1.Upload()

            f1 = None


    def run(self, host='127.0.0.1', port=9001, autoInstallPrinter=True):
        """
		normally all the default values are exactly what you need!
		autoInstallPrinter is used to install the printer in the operating system
		(currently only supports Windows)
		startServer is required for this
		"""
        import printServer
        self._server = printServer.PrintServer(self.name, host, port, autoInstallPrinter, self.printPostscript)
        self._server.run()
        del self._server  # delete it so it gets un-registered
        self._server = None

    def _postscriptToFormat(self, data, gsDev='pdfwrite', gsDevOptions=None, outputDebug=True):
        """
		Converts postscript data (in a string) to pdf data (in a string)
		gsDev is a ghostscript format device
		For ghostscript command line, see also:
			http://www.ghostscript.com/doc/current/Devices.htm
			http://www.ghostscript.com/doc/current/Use.htm#Options
		"""
        if gsDevOptions is None:
            gsDevOptions = []
        args = [
            "-q", "-dNOPAUSE","-dBATCH", "-sDEVICE=pdfwrite",
            "-sstdout=%stderr",
            "-sOutputFile=" + "I_printed_this.pdf",
            "-f", "I_printed_this.ps"

        ]
        encoding = locale.getpreferredencoding()
        args = [a.encode(encoding) for a in args]

        ghostscript.Ghostscript(*args)

        # args = b"""test.py
        #      -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite -sOutputFile=E:\\virtualprinter2\\I_printed_this.pdf
        #     -c .setpdfwrite""".split()
        #
        # with ghostscript.Ghostscript(*args) as gs:
        #     gs.run_string(data)

        # if gsDevOptions is None:
        #     gsDevOptions = []
        # cmd = GHOSTSCRIPT_APP + ' -q  -sDEVICE=' + gsDev + ' '
        # cmd = cmd + (' '.join(gsDevOptions)) + ' -sstdout=%stderr -sOutputFile=- -dBATCH -'
        # if outputDebug:
        #     print(cmd)
         #po = subprocess.Popen(str(ghostscript.Ghostscript(*args)), stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                               #stdout=subprocess.PIPE, shell=True)
         #data, gsStdoutStderr = po.communicate(input=bytes(data, encoding='latin-1'))
        # if outputDebug:
        #     print(gsStdoutStderr)  # note: stdout also goes to stderr because of the -sstdout=%stderr flag
        return data

    def printPostscript(self, datasource, datasourceIsFilename=False,
                        title=None, author=None, filename=None):
        """
		datasource is either:
			a filename
			None to get data from stdin
			a file-like object
			something else to convert using str() and then print
		Keep in mind that it MUST contain postscript data
		"""
        # -- open data source
        data = None
        if datasource is None:
            #print("i am here")
            data = sys.stdin.buffer.read()
        elif isinstance(datasource, str):
            #print("i am here")
            if datasourceIsFilename:
                #print("i am here")
                f = open(datasource, 'rb')
                data = f.read()
                f.close()
                if title is None:
                   title = datasource.rsplit(os.sep, 1)[-1].rsplit('.', 1)[0]
            else:
                #print("i am here")
                data = datasource
        elif hasattr(datasource, 'read'):
            print("i am here")
            data = datasource.buffer.read()
        else:
            #print("i am here")
            #data = str(datasource)
            data = str(datasource)
        # -- convert the data to the required format
        print('Converting data...')
        gsDevOptions = []
        if self.acceptsFormat == 'pdf':
            gsDev = 'pdfwrite'
        elif self.acceptsFormat == 'png':
            gsDevOptions.append('-r600')
            gsDevOptions.append('-dDownScaleFactor=3')
            if self.acceptsColors == 'grey':
                gsDev = 'pnggray'
            elif self.acceptsColors == 'rgba':
                if self.bgColor is None:  # I'm not sure how necessary background color is
                    self.bgColor = '#ffffff'
                gsDev = 'pngalpha'
                if self.bgColor != None:
                    if self.bgColor[0] != '#':
                        self.bgColor = '#' + self.bgColor
                    gsDevOptions.append('-dBackgroundColor=16' + self.bgColor)
            # elif self.acceptsColors=='rgb': #TODO
            else:
                raise Exception('Unacceptable color format "' + self.acceptsColors + '"')
        else:
            raise Exception('Unacceptable data type format "' + self.acceptsFormat + '"')
        data = self._postscriptToFormat(data, gsDev, gsDevOptions)
        # -- send the data to the printThis function
        print('Printing data...')
        self.printThis(data, title=title, author=author)



if __name__ == '__main__':
    import sys
    p = Printer()
    p.run()
    # usage =

    """
    USAGE:
        virtualPrinter filename.ps ..... to print a file
        virtualPrinter - ............... to print postscript piped in from stdin
        virtualPrinter ip[:port]........ to start a print server
    NOTE:
        you can do multiple commands with the same virtualPrinter
    """


    # if len(sys.argv) < 2:
    #     print(usage)
    # else
    #     p = Printer()
    #     for arg in sys.argv[1:]:
    #         if arg == '-':
    #             p.printPostscript(sys.stdin)
    #         elif arg.find(os.sep) < 0 and len(sys.argv[1].split('.')) > 2:
    #             # looks like an ip to me!
    #             ip = arg.rsplit(':', 1)
    #             if len(ip) > 1:
    #                 port = ip[-1]
    #             else:
    #                 port = None
    #             ip = ip[0]
    #             p.run(ip, port)
    #         else:
    #             p.printPostscript(arg, True)


