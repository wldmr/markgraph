def task_test():
    return {
        'actions': ['markgraph.py test.txt'],
        'verbosity': 2,
    }

def task_graph():
    return {
        'actions': ['markgraph.py test.txt | dot -Tpdf -otest.pdf'],
    }
