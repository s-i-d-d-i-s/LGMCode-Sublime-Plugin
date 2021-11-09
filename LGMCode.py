import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import _thread
import threading
import platform
import os

isWindows = platform.system() == "Windows"



def getDelim():
    if isWindows:
        return '\\'
    else:
        return '/'



def getParsedTC(filename):
    tests = json.loads(open(filename+"_tests.txt",'r').read())
    idx = 1
    res = "Test Cases Parsed !\n----------\n\n"
    for x in tests:
        res += "Input {}:\n{}\nExpected {}:\n{}\n\n----------\n\n".format(idx,x["test"],idx,x["correct_answers"][0])
        idx+=1
    return res.strip()




def updateStatus(file_name):
    parsedTC = getParsedTC(file_name)
    folder_path = getDelim().join(file_name.split(getDelim())[:-1])
    status_path = folder_path+getDelim()+'status.txt'
    with open(status_path,'w') as f:
        f.write(parsedTC)



def updateIO(input_tc, output_tc, file_name):
    folder_path = getDelim().join(file_name.split(getDelim())[:-1])
    input_path = folder_path+getDelim()+'input.txt'
    output_path = folder_path+getDelim()+'output.txt'
    with open(input_path,'w') as f:
        f.write(input_tc)
    with open(output_path,'w') as f:
        f.write(output_tc)




def getSummary(verdicts):
    summary=""
    for i in range(len(verdicts)):
        summary += "Test #{}: {}".format(i+1,"Accepted" if verdicts[i]==True else "Wrong Answer")
        summary += "\n"
    return summary



def getStatus(tests,folder_path,file_name):
    tests = json.loads(tests)
    idx,verdicts,res= 1, [],""
    for x in tests:
        output,verdict = getTC(x,idx,folder_path,file_name)
        verdicts.append(verdict)
        res += "{}\n\n----------\n\n".format(output)
        idx+=1
    summary = getSummary(verdicts)
    res = summary + "\n----------\n"+res
    return res





def MakeHandlerClassFromFilename(filename):
    class HandleRequests(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                tests = json.loads(body.decode('utf8'))
                tests = tests["tests"]
                ntests = []
                for test in tests:
                    ntest = {
                        "test": test["input"],
                        "correct_answers": [test["output"].strip()]
                    }
                    ntests.append(ntest)
                nfilename = filename + "_tests.txt"

                ## Write the Tests to a file                
                with open(nfilename, "w") as f:
                    f.write(json.dumps(ntests))

                ## Fill Initial Input/Output
                input_tc = ntests[0]['test'].strip()
                output_tc = ntests[0]['correct_answers'][0].strip()


                ## Update IO
                updateIO(input_tc,output_tc,filename)
                ## Update Status
                updateStatus(filename)

            except Exception as e:
                print("Error handling POST - " + str(e))
            threading.Thread(target=self.server.shutdown, daemon=True).start()
    return HandleRequests


class CompetitiveCompanionServer:
    def startServer(filename):
        host = 'localhost'
        port = 12345
        HandlerClass = MakeHandlerClassFromFilename(filename)
        httpd = HTTPServer((host, port), HandlerClass)
        httpd.serve_forever()
        print("Server has been shutdown")


class ccompanionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:            
            _thread.start_new_thread(CompetitiveCompanionServer.startServer,(self.view.file_name(),))
        except Exception as e:
            print("Error: unable to start thread - " + str(e))


def getTC(testcase,index,folder_path,file_name):
    res = "Input {}:\n{}\nExpected {}:\n{}\n".format(index,testcase["test"],index,testcase["correct_answers"][0])
    test_case_path = folder_path+getDelim()+'temp_tc.txt'
    with open(test_case_path,'w') as f:
        f.write(testcase['test'])
    os.chdir(folder_path)
    run_command = getRunCommand(file_name,getLanguage(file_name))
    os.system(run_command)
    output = open('temp_op.txt').read()
    res += "\nOutput {}:\n{}".format(index,output)
    verd = output.strip() == testcase["correct_answers"][0].strip()
    os.remove('temp_op.txt')
    os.remove('temp_tc.txt')
    return res,verd
    
def getLanguage(filename):
    extension = filename.split('.')[-1]
    if extension == 'cpp':
        return 'C++'
    return "Unknown Language"

def getCompileCommand(file_name,language):
    if language == 'C++':
        return 'g++ -std=c++14 {} -o {}'.format(file_name,file_name.split('.')[0])
    return 'echo UnknownLanguage'

def getRunCommand(file_name,language):
    if language == 'C++':
        return '{} < temp_tc.txt > temp_op.txt'.format(file_name.split('.')[0])
    return 'echo UnknownLanguage'

def compileAndRunCode(_fileName,tests):
    folder_path = getDelim().join(_fileName.split(getDelim())[:-1])
    file_name = _fileName.split(getDelim())[-1]
    language = getLanguage(file_name)


    if language == "Unknown Language":
        with open(folder_path+getDelim()+'status.txt','w') as f:
            f.write("Unknown Language")
        return

    os.chdir(folder_path)
    compile_command = getCompileCommand(file_name,language)

    print("Language: {}, Compile Command: {}".format(language,compile_command))
    os.system(compile_command)

    with open(folder_path+getDelim()+'status.txt','w') as f:
        f.write(getStatus(tests,folder_path,file_name))

class lgmcoderunnerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        tests = self.view.file_name()+"_tests.txt"
        tests = open(tests,'r').read()
        compileAndRunCode(self.view.file_name(),tests)
        
