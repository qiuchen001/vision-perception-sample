import time
from functools import wraps
from bdp_api.bdp_logger import logger as bdp_logger

def logtime(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        start=time.time()
        bdp_logger.info('job start ')
        if len(args)>0:
            bdp_logger.info('inputmsg is:'+str(args))
        try:
            result= func(*args,**kwargs)
            bdp_logger.info('the result of job:'+str(result))
            end= time.time()
            bdp_logger.info('job end ' )
            
            bdp_logger.info('任务执行耗时：'+('%.2f' % (end-start))+'s')
            bdp_logger.finish('job done')
            return result
        except Exception as e:
            bdp_logger.error('job execute error! msg:'+str(e))
    return wrapper