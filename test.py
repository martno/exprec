import runner


def main():
    with runner.Experiment('', tags=['test-tag1', 'tag2']) as proc:
        print('hello')


main()
