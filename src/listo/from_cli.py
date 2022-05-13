import argparse
from .daemon import Listo


def run_from_cli():
    app_name = """ 
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                                       
    |        |             ..'''' `````|`````  .^^^^^^^^.
    |        |          .''            |      |          |
    |        |       ..'               |      |          |
    |_______ | ....''                  |       `.______.'
    
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::
    """
    usage = 'Listo'
    description = '''
    Listo can send a post/notification to Discord when a new episode releases. 
    The module keeps track of all non-adult (hentai) Anime releasing in the next 24 hours.
    '''

    parser = argparse.ArgumentParser(
        prog='Listo',
        usage='',
        description=f'{app_name}\n\n{description}',
        formatter_class=argparse.RawDescriptionHelpFormatter
        )
    
    parser.add_argument('webhook', type=str, help='Discord webhook endpoint')
    parser.add_argument('-a', '--all', action='store_true', help='allow "anime" from all countries')
    parser.add_argument('-i', '--hentai', action='store_true', help='allow hentai')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose logging')
    args = parser.parse_args()

    print(app_name)

    app = Listo(
        webhook=args.webhook, 
        allow_all_anime=args.all, 
        allow_hentai=args.hentai,
        verbose=args.verbose
        )
    
    app.run()

if __name__ == '__main__':
    run_from_cli()