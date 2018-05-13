from exprec import runner


def main():
    with runner.Experiment('', tags=['test-tag1', 'tag2']) as experiment:
        print('hello')

        raise ValueError('test')

        with experiment.open('test.txt', mode='r', uuid='ef22bde6-4e11-11e8-84ea-54e1adcfa8e2') as fp:
            print(fp.read())
        
        print ('hello')



main()
