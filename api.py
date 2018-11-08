import json
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, abort
from flask_redis import FlaskRedis

app = Flask(__name__)
app.config.update({
    'REDIS_URL': "unix://abrakadabra@/var/run/redis/redis-server.sock?db=0"
})
redis_store = FlaskRedis(app)


@app.route('/api/nodes/<string:ip>/<int:port>/peers', methods=['GET'])
def get_node_info(ip, port):
    map_key = "node-map:{}-{}".format(ip, port)
    node_data_serialized = redis_store.get(map_key)
    if node_data_serialized is None:
        abort(404)
    node_data = json.loads(node_data_serialized)
    return jsonify({'node': '{}:{}'.format(ip, port), 'peers': node_data})


if __name__ == '__main__':
    formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('api.log', maxBytes=1000000, backupCount=3)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=False)
