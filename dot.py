from subprocess import Popen, PIPE

def call_dot(filename, filetype, string):
    p = Popen(['dot', '-T'+filetype, '-o'+filename], stdin=PIPE)
    p.communicate(string)
