import logging

__version__ = '0.1.0'
logging.basicConfig(
    filename='game.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
