class Config:
    USE_UNTESTED_FUNCTIONS = False


def assert_use_untested_functions():
    assert Config.USE_UNTESTED_FUNCTIONS, 'this function is not tested yet. You can turn on Config.USE_UNTESTED_FUNCTIONS to use it.'
