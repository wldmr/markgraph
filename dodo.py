def task_Readme():
    return {
        'actions': ['markgraph.py Readme.md', 'pandoc Readme.md > Readme.html'],
        'file_dep': ['markgraph.py', 'Readme.md'],
        'verbosity': 2,
    }


def task_Markdown():
    return {
        'actions': ['python mdx_markgraph.py Readme.md > Readme.html'],
        'file_dep': ['mdx_markgraph.py', 'Readme.md'],
        'verbosity': 2,
    }
