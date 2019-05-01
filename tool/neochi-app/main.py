import redis
import time

time.sleep(3)

r = redis.StrictRedis(host='localhost')
r.publish('start_ir_receiving', 3)
print('data sent')

#time.sleep(5000)