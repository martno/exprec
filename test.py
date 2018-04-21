import runner


def main():
    with runner.Procedure('test') as proc:
        print('hello')


main()
