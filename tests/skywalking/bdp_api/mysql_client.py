# -*- coding: utf-8 -*-
#from sqlalchemy import create_engine, util
#from sqlalchemy import func as func
#from sqlalchemy import or_ as or_
#from sqlalchemy import and_ as and_
#from sqlalchemy.orm import sessionmaker
#from urllib import parse
#import os


#class MysqlConnection:
#    def __init__(self, db_name=None, app_key=None, pwd=None, k8s_master_host="10.66.12.37"):
#        env = os.getenv("BDP_ENV")
#        open_logs = False
#        if env == "dev": # 在k8s内部访问
#            host = "mysql-business-0.mysql-business"
#            port = 3306
#            open_logs = True
#        elif env == "prod": # 在k8s内部访问
#            host = "mysql-business-0.mysql-business"
#            port = 3306
#        else: # 没有env，则视为在k8s外部访问，仅可访问prod环境
#            host = k8s_master_host
#            port = 30190
#        if db_name is None:
#            db_name = "public"
#        if app_key is None:
#            app_key = "bdp_public"
#        if pwd is None:
#            pwd = "Jg!s%b[_2q"
#        pwd = parse.quote_plus(pwd)
#        
#        url = "mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(app_key, pwd, host, port, db_name)
#        engine = create_engine(
#            url
#            , encoding="utf-8"
#            , echo=open_logs
#            , max_overflow=8)
#        Session = sessionmaker(bind=engine)
#        self.__session = Session()
#
#    def __del__(self):
#        if self.__session is not None:
#            self.__session.close()
#
#    def query(self, *entities, **kwargs):
#        return self.__session.query(*entities, **kwargs)
#
#    def add(self, instance, _warn=True):
#        return self.__session.add(instance, _warn)
#
#    def add_all(self, instances):
#        return self.__session.add_all(instances)
#
#    def delete(self, instance):
#        return self.__session.delete(instance)
#
#    def commit(self):
#        try:
#            return self.__session.commit()
#        except:
#            self.__session.rollback()
#
#    def execute(self, statement, params=None, execution_options=util.EMPTY_DICT, bind_arguments=None):
#        return self.__session.execute(statement, params, execution_options, bind_arguments)
#
#    def rollback(self):
#        return self.__session.rollback()
#
#    def close(self):
#        return self.__session.close()
