def task_Readme():
    return {
        'actions': ['markgraph.py Readme.md', 'pandoc Readme.md > Readme.html'],
        'file_dep': ['markgraph.py', 'Readme.md'],
        'verbosity': 2,
    }
