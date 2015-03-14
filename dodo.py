def task_Readme():
    return {
        'actions': ['markgraph.py Readme.txt', 'pandoc Readme.txt > Readme.html'],
        'file_dep': ['markgraph.py', 'Readme.txt'],
        'verbosity': 2,
    }
