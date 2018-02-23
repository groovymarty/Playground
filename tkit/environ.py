# tbox.environ

def set_logger(env, logger):
    if env is not None:
        env['logger'] = logger

def log_info(env, msg):
    if env and 'logger' in env:
        env['logger'].log_info(msg)

def log_error(env, msg):
    if env and 'logger' in env:
        env['logger'].log_error(msg)

def log_warning(env, msg):
    if env and 'logger' in env:
        env['logger'].log_warning(msg)
