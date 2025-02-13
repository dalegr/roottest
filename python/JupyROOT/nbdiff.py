import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile

nbExtension=".ipynb"
convCmdTmpl = "%s nbconvert  --to notebook --ExecutePreprocessor.kernel_name=%s --ExecutePreprocessor.enabled=True --ExecutePreprocessor.timeout=3600 %s --output %s"
pythonInterpName = 'python3' if sys.version_info >= (3, 0) else 'python2'

rootKernelFileContent = '''{
 "language": "c++",
 "display_name": "ROOT C++",
 "argv": [
  "%s",
  "-m",
  "JupyROOT.kernel.rootkernel",
  "-f",
  "{connection_file}"
 ]
}
''' %pythonInterpName



# Replace the criterion according to which a line shall be skipped
def customLineJunkFilter(line):
    # Skip the banner and empty lines
    junkLines =['Info in <TUnixSystem::ACLiC',
                'Info in <TMacOSXSystem::ACLiC',
                'Welcome to JupyROOT 6.',
                'FAILED TO establish the default connection to the WindowServer',
                '"version": ',
                '"pygments_lexer": "ipython']
    for junkLine in junkLines:
        if junkLine in line: return False
    return True

def getFilteredLines(fileName):
    filteredLines = list(filter(customLineJunkFilter, open(fileName).readlines()))
    # Sometimes the jupyter server adds a new line at the end of the notebook
    # and nbconvert does not.
    lastLine = filteredLines[-1]
    if lastLine[-1] != "\n": filteredLines[-1] += "\n"
    return filteredLines

def compareNotebooks(inNBName,outNBName):
    inNBLines = getFilteredLines(inNBName)
    outNBLines = getFilteredLines(outNBName)
    areDifferent = False
    for line in difflib.unified_diff(inNBLines, outNBLines, fromfile=inNBName, tofile=outNBName):
        areDifferent = True
        sys.stdout.write(line)
    if areDifferent: print("\n")
    return areDifferent

def createKernelSpec():
    """Create a root kernel spec with the right python interpreter name
    and puts it in a tmp directory. Return the name of such directory."""
    tmpd = tempfile.mkdtemp(suffix="_nbdiff_ipythondir")
    kernelsPath = os.path.join(tmpd, "kernels")
    os.mkdir(kernelsPath)
    rootKernelPath = os.path.join(kernelsPath, "root")
    os.mkdir(rootKernelPath)
    kernel_file = open(os.path.join(rootKernelPath, "kernel.json"), "w")
    kernel_file.write(rootKernelFileContent)
    kernel_file.close()

    return tmpd

def addEtcToEnvironment(inNBDirName):
    """Add the etc directory of root to the environment under the name of
    JUPYTER_PATH in order to pick up the kernel specs.
    """
    ipythondir = createKernelSpec()
    os.environ["JUPYTER_PATH"] = ipythondir
    os.environ["IPYTHONDIR"] = ipythondir
    return ipythondir

def getInterpreterName():
    """Find if the 'jupyter' executable is available on the platform. If
    yes, return its name else return 'ipython'
    """
    ret = subprocess.call("type jupyter",
                          shell=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return "jupyter" if ret == 0 else "i%s" %pythonInterpName

def getKernelName(inNBName):
    nbj = json.load(open(inNBName))
    if nbj["metadata"]["kernelspec"]["language"] == "python":
        return pythonInterpName
    else: # we support only Python and C++
        return 'root'


def canReproduceNotebook(inNBName):
    kernelName = getKernelName(inNBName)
    tmpDir = addEtcToEnvironment(os.path.dirname(inNBName))
    outNBName = inNBName.replace(nbExtension,"_out"+nbExtension)
    interpName = getInterpreterName()
    convCmd = convCmdTmpl %(interpName, kernelName, inNBName, outNBName)
    os.system(convCmd) # we use system to inherit the environment in os.environ
    shutil.rmtree(tmpDir)
    return compareNotebooks(inNBName,outNBName)

def isInputNotebookFileName(filename):
    if not filename.endswith(".ipynb"):
        print("Notebook files shall have the %s extension" %nbExtension)
        return False
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: nbdiff.py myNotebook.ipynb")
        sys.exit(1)
    nbFileName = sys.argv[1]
    if not isInputNotebookFileName(nbFileName):
        sys.exit(1)
    retCode = canReproduceNotebook(nbFileName)
    sys.exit(retCode)
