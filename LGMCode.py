import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import _thread
import threading
import platform
import os

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
                if platform.system() == "Windows":
                    nfilename = filename + "_tests.txt"
                print(nfilename)
                
                with open(nfilename, "w") as f:
                    f.write(json.dumps(ntests))
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
            _thread.start_new_thread(CompetitiveCompanionServer.startServer,
                                     (self.view.file_name(),))
            
        except Exception as e:
            print("Error: unable to start thread - " + str(e))


def getTC(testcase,index,folder_path,file_name):
    res = "Input {}:\n{}\nExpected {}:\n{}\n".format(index,testcase["test"],index,testcase["correct_answers"][0])
    test_case_path = folder_path+'/temp_tc.txt'
    with open(test_case_path,'w') as f:
        f.write(testcase['test'])
    if platform.system() == "Windows":
        pass
    else:
        os.chdir(folder_path)
        file_name = file_name.split('.')[0]
        file_name = './{} < {} > temp_op.txt'.format(file_name,test_case_path)
        os.system(file_name)
        output = open('temp_op.txt').read()
        res += "\nOutput {}:\n{}".format(index,output)
        verd = output.strip() == testcase["correct_answers"][0].strip()
        os.remove('temp_op.txt')
        os.remove('temp_tc.txt')
        return res,verd

    return res,False

def getStatus(tests,folder_path,file_name):
    tests = json.loads(tests)
    idx = 1
    verds = []
    res = ""
    for x in tests:
        op,verd = getTC(x,idx,folder_path,file_name)
        verds.append(verd)
        res += op
        res += "\n"
        res += "\n----------\n"
        res += "\n"
        idx+=1
    summary = ""
    for i in range(len(verds)):
        verd = verds[i]
        if verd :
            verd = "Accepted"
        else:
            verd = "Wrong Answer"
        summary += "Test #{}: {}".format(i+1,verd)
        summary += "\n"

    res = summary + "\n----------\n"+res
    return res

def updateStatus(file_name):
    parsedTC = getParsedTC(file_name)
    folder_path = '/'.join(file_name.split('/')[:-1])
    with open(folder_path+'/status.txt','w') as f:
        f.write(parsedTC)

def getParsedTC(filename):
    tests = filename+"_tests.txt"
    tests = open(tests,'r').read()
    tests = json.loads(tests)
    idx = 1
    res = "Test Cases Parsed !\n----------\n\n"
    for x in tests:
        res += "Input {}:\n{}\nExpected {}:\n{}".format(idx,x["test"],idx,x["correct_answers"][0])
        res += "\n"
        res += "\n----------\n"
        res += "\n"
        idx+=1
    return res.strip()
class lgmcoderunnerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        tests = self.view.file_name()+"_tests.txt"
        tests = open(tests,'r').read()
        folder_path = '/'.join(self.view.file_name().split('/')[:-1])
        file_name = self.view.file_name().split('/')[-1]
        os.chdir(folder_path)
        if platform.system() == "Windows":
            pass
        else:
            compile_command = 'g++ -std=c++14 {} -o {}'.format(file_name,file_name.split('.')[0])
            print(compile_command)
            os.system(compile_command)
        with open(folder_path+'/status.txt','w') as f:
            f.write(getStatus(tests,folder_path,file_name))