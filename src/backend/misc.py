import logging

def createLogger(name):
    iname = (name + ' ' * 16)[:16]
    logger = logging.getLogger(iname)
    logger.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s',
                                  datefmt = '%Y/%m/%d %H:%M:%S')
    # Create file handler
    fileHandler = logging.FileHandler(filename = f'{name}.log',
                                      mode = 'w'
                                      )
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)

    # Create console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    return logger

