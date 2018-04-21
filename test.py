import runner


def main():
    with runner.Procedure('test2') as proc:
        print('hello')


main()
