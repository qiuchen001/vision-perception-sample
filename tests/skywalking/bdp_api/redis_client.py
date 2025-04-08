# -*- coding: utf-8 -*-
import redis
import requests
import json
import os

class RedisCategory:
    def __init__(self, category_name, project_name=None, appkey=None, k8s_master_host="cybertron-redis"):
        env = os.getenv("BDP_ENV")
        if env == "dev": # 在k8s内部访问
            validation_service_url = "http://storage-manager-service:8080/redis"
            redis_cluster_url = "redis-business-public-0.redis-business-public"
            redis_port = 6379
        elif env == "prod":
            validation_service_url = "http://storage-manager-service:8080/redis"
            redis_cluster_url = "cybertron-redis"
            redis_port = 6379
        else: # 没有env，则视为在k8s外部访问，仅可访问default环境
            validation_service_url = "http://" + k8s_master_host + ":30080/default/redissvc/redis"
            redis_cluster_url = k8s_master_host
            redis_port = 30191
        if project_name is None or project_name == '':
            project_name = "public"
        if category_name is None or category_name.strip() == '':
            raise RuntimeError("categoryName must not be empty!")
        try:
            redis_validation_service_uri = validation_service_url + "/categories/{0}?project-name={1}".format(category_name, project_name)
            response = requests.get(redis_validation_service_uri)
            if response is None or response.status_code != 200:
                raise RuntimeError('Redis category "' + project_name + "-" + category_name + '" not found.')
            category_info = json.loads(response.content)["category"]
            authed = True
            if category_info["enableAuthorization"] == 1:
                authedAppkeys = category_info["authedAppKeys"]
                if authedAppkeys is not None and authedAppkeys != '':
                    if appkey is None or appkey not in authedAppkeys.split(","):
                        authed = False
                else:
                    authed = False
            if not authed:
                if appkey is None:
                    raise RuntimeError('Redis category "' + project_name + "-" + category_name + '" authorization denied with empty appkey, please contact ' + category_info["owners"])
                else:
                    raise RuntimeError(
                        'Redis category "' + project_name + "-" + category_name + '" authorization denied with appkey "' + appkey + '", please contact ' +
                        category_info["owners"])
        except:
            raise RuntimeError("Could not validate redis category: " + project_name + "-" + category_name)

        try:
            pool = redis.ConnectionPool(host=redis_cluster_url, port=redis_port, decode_responses=True, password='pi*R3!{Qmc8@9')
            self.__client = redis.Redis(connection_pool = pool)
            self.__project_name = project_name.strip()
            self.__category_name = category_name.strip()
            self.__expire_ms = category_info["expireMs"]
            if self.__expire_ms <= 0:
                self.__expire_ms = None
        except:
            raise RuntimeError("Could not connect to redis cluster.")
    def __del__(self):
        if self.__client is not None:
            self.__client.close()

    def exists(self, key):
        if key is None or key == '':
            return False
        if self.__client.exists(self.__wrapKey(key)) == '1':
            return True
        else:
            return False

    def delete(self, key):
        if key is None or key == '':
            return None
        return self.__client.delete(self.__wrapKey(key))

    def expire(self, key, ms):
        if key is None or key == '':
            return None
        return self.__client.pexpire(self.__wrapKey(key), ms)

    def type(self, key):
        if key is None or key == '':
            return None
        return self.__client.type(self.__wrapKey(key))

    def set(self, key, value, expire_ms = None, nx=False, xx=False):
        if key is None or key == '' or value is None:
            return None
        if expire_ms is None or expire_ms <= 0:
            expire_ms = None
        if expire_ms is None:
            expire_ms = self.__expire_ms

        return self.__client.set(name = self.__wrapKey(key), value=value, px=expire_ms, ex=None, nx=nx, xx=xx)

    def setnx(self, key, value):
        if key is None or key == '' or value is None:
            return None
        return self.__client.setnx(self.__wrapKey(key), value)

    def get(self, key):
        return self.__client.get(self.__wrapKey(key))

    def getset(self, key, value):
        if key is None or key == '' or value is None:
            return None
        return self.__client.getset(self.__wrapKey(key), value)

    def mset(self, kvsInDict):
        if kvsInDict is None:
            return None
        tmp = {}
        for k in kvsInDict.keys():
            tmp[self.__wrapKey(k)] = kvsInDict[k]
        return self.__client.mset(tmp)

    def mget(self, keys):
        if keys is None:
            return None
        wrappedKeys = [self.__wrapKey(k) for k in keys]
        values = self.__client.mget(wrappedKeys)
        result = {}
        for i, value in enumerate(values):
            result[keys[i]] = value
        return result

    def strlen(self, key):
        if key is None or key == '':
            return 0
        return self.__client.strlen(self.__wrapKey(key))

    def incr(self, key, amount = 1):
        if key is None or key == '':
            return None
        return self.__client.incr(self.__wrapKey(key), amount)

    def incrbyfloat(self, key, amount=1.0):
        if key is None:
            return None
        return self.__client.incrbyfloat(self.__wrapKey(key), amount)

    def decr(self, key, amount=1):
        if key is None or key == '':
            return None
        return self.__client.decr(self.__wrapKey(key), amount)

    def append(self, key, value):
        if key is None or key == '':
            return None
        if value is None or value == '':
            return None
        return self.__client.append(self.__wrapKey(key), value)

    def hset(self, key, subkey, value):
        if key is None or key == '':
            return None
        if subkey is None or subkey == '':
            return None
        if value is None:
            return None
        return self.__client.hset(self.__wrapKey(key), subkey, value)

    def hset_multi(self, key, kvsInDict):
        if kvsInDict is None:
            return None
        return self.__client.hset(name=self.__wrapKey(key), mapping=kvsInDict)

    def hget(self, key, subkey):
        if key is None or key == '':
            return None
        if subkey is None or subkey == '':
            return None
        return self.__client.hget(name=self.__wrapKey(key), key=subkey)

    def hget_multi(self, key, subKeys):
        if key is None or key == '':
            return None
        if subKeys is None:
            return None
        return self.__client.hmget(name=self.__wrapKey(key), keys=subKeys)

    def hgetall(self, key):
        if key is None or key == '':
            return None
        return self.__client.hgetall(name=self.__wrapKey(key))

    def hsubkeys(self, key):
        if key is None or key == '':
            return None
        return self.__client.hkeys(name=self.__wrapKey(key))

    def hvals(self, key):
        if key is None or key == '':
            return None
        return self.__client.hvals(name=self.__wrapKey(key))

    def hexists(self, key, subkey):
        if key is None or key == '':
            return False
        if subkey is None or subkey == '':
            return False
        return self.__client.hexists(name=self.__wrapKey(key), key=subkey)

    def hdel(self, key, *subkeys):
        if key is None or key == '':
            return None
        if subkeys is None:
            return None
        return self.__client.hdel(self.__wrapKey(key), *subkeys)

    def hincrby(self, key, subkey, amount=1):
        if key is None or key == '':
            return None
        if subkey is None or subkey == '':
            return None
        return self.__client.hincrby(name=self.__wrapKey(key), key=subkey, amount=amount)

    def hincrbyfloat(self, key, subkey, amount=1.0):
        if key is None or key == '':
            return None
        if subkey is None or subkey == '':
            return None
        return self.__client.hincrbyfloat(name=self.__wrapKey(key), key=subkey, amount=amount)

    def hscan_iter(self, key, match=None, count=None):
        if key is None or key == '':
            return None
        return self.__client.hscan(name=self.__wrapKey(key), match=match, count=count)

    def llpush(self, key, *values):
        if key is None or key == '':
            return None
        if values is None:
            return None
        return self.__client.lpush(self.__wrapKey(key), *values)

    def lrpush(self, key, *values):
        if key is None or key == '':
            return None
        if values is None:
            return None
        return self.__client.rpush(self.__wrapKey(key), *values)

    def linsert(self, key, where, refvalue, value):
        if key is None or key == '':
            return None
        if refvalue is None:
            return None
        if value is None:
            return None
        return self.__client.linsert(self.__wrapKey(key), where, refvalue, value)

    def lset(self, key, index, value):
        if key is None or key == '':
            return None
        if value is None:
            return None
        return self.__client.lset(self.__wrapKey(key), index, value)

    def lrem(self, key, value, num):
        if key is None or key == '':
            return None
        if value is None:
            return None
        return self.__client.lrem(self.__wrapKey(key), num, value)

    def llpop(self, key):
        if key is None or key == '':
            return None
        return self.__client.lpop(self.__wrapKey(key))

    def lrpop(self, key):
        if key is None or key == '':
            return None
        return self.__client.rpop(self.__wrapKey(key))

    def lrange(self, key, start, end):
        if key is None or key == '':
            return None
        return self.__client.lrange(self.__wrapKey(key), start, end)


    def ltrim(self, key, start, end):
        if key is None or key == '':
            return None
        return self.__client.ltrim(self.__wrapKey(key), start, end)

    def lindex(self, key, index):
        if key is None or key == '':
            return None
        return self.__client.lindex(self.__wrapKey(key), index)

    def llen(self, key):
        if key is None or key == '':
            return None
        return self.__client.llen(self.__wrapKey(key))

    def sadd(self, key, *values):
        if key is None or key == '':
            return None
        if values is None:
            return None
        return self.__client.sadd(self.__wrapKey(key), *values)

    def ssize(self, key):
        if key is None or key == '':
            return None
        return self.__client.scard(self.__wrapKey(key))

    def smembers(self, key):
        if key is None or key == '':
            return None
        return self.__client.smembers(self.__wrapKey(key))

    def sdiff(self, key1, key2):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        return self.__client.sdiff(self.__wrapKey(key1), self.__wrapKey(key2))

    def sdiffstore(self, key1, key2, result_key):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        if result_key is None or result_key == '':
            return None
        return self.__client.sdiffstore(self.__wrapKey(result_key), self.__wrapKey(key1), self.__wrapKey(key2))

    def sinter(self, key1, key2):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        return self.__client.sinter(self.__wrapKey(key1), self.__wrapKey(key2))

    def sinterstore(self, key1, key2, result_key):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        if result_key is None or result_key == '':
            return None
        return self.__client.sinterstore(self.__wrapKey(result_key), self.__wrapKey(key1), self.__wrapKey(key2))

    def sunion(self, key1, key2):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        return self.__client.sunion(self.__wrapKey(key1), self.__wrapKey(key2))

    def sunionstore(self, key1, key2, result_key):
        if key1 is None or key1 == '':
            return None
        if key2 is None or key2 == '':
            return None
        if result_key is None or result_key == '':
            return None
        return self.__client.sunionstore(self.__wrapKey(result_key), self.__wrapKey(key1), self.__wrapKey(key2))

    def sismember(self, key, value):
        if key is None or key == '':
            return None
        if value is None:
            return None
        return self.__client.sismember(self.__wrapKey(key), value)

    def smove(self, src_key, dst_key, value):
        if src_key is None or src_key == '':
            return None
        if dst_key is None or dst_key == '':
            return None
        if value is None:
            return None
        return self.__client.smove(self.__wrapKey(src_key), self.__wrapKey(dst_key), value)

    def spop(self, key):
        if key is None or key == '':
            return None
        return self.__client.spop(self.__wrapKey(key))

    def zadd(self, key, values_with_scores, nx=False, xx=False, ch=False, incr=False):
        if key is None or key == '':
            return None
        if values_with_scores is None:
            return None
        return self.__client.zadd(self.__wrapKey(key), values_with_scores, nx, xx, ch, incr)

    def zsize(self, key):
        if key is None or key == '':
            return None
        return self.__client.zcard(self.__wrapKey(key))

    def zrange(self, key, start, end, desc=False, withscores=False, score_cast_func=float):
        if key is None or key == '':
            return None
        return self.__client.zrange(self.__wrapKey(key), start, end, desc, withscores, score_cast_func)

    def zrangebyscore(self, key, min, max, start=None, num=None, withscores=False, score_cast_func=float):
        if key is None or key == '':
            return None
        return self.__client.zrangebyscore(self.__wrapKey(key), min, max, start, num, withscores, score_cast_func)

    def zcount(self, key, min, max):
        if key is None or key == '':
            return None
        return self.__client.zcount(self.__wrapKey(key), min, max)

    def zincrby(self, key, value, amount):
        if key is None or key == '':
            return None
        if value is None:
            return None
        return self.__client.zincrby(self.__wrapKey(key), amount, value)

    def zrank(self, key, value):
        if key is None or key == '':
            return None
        return self.__client.zrank(self.__wrapKey(key), value)

    def zrem(self, key, *values):
        if key is None or key == '':
            return None
        if values is None:
            return None
        return self.__client.zrem(self.__wrapKey(key), *values)

    def zremrangebyrank(self, key, min, max):
        if key is None or key == '':
            return None
        return self.__client.zremrangebyrank(self.__wrapKey(key), min, max)

    def zremrangebyscore(self, key, min, max):
        if key is None or key == '':
            return None
        return self.__client.zremrangebyscore(self.__wrapKey(key), min, max)

    def zscore(self, key, value):
        if key is None or key == '':
            return None
        return self.__client.zscore(self.__wrapKey(key), value)

    def __wrapKey(self, key):
        return self.__project_name + "_" + self.__category_name + "_" + key