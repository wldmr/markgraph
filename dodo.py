def task_test():
    return {
        'actions': ['markgraph.py test.txt', 'markdown_py test.txt > test.html'],
        'verbosity': 2,
    }

def task_graph():
    return {
        'actions': ['markgraph.py test.txt'],
    }
