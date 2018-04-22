import runner


def main():
    with runner.Procedure('', tags=['test-tag1', 'tag2']) as proc:
        print('hello')


main()
